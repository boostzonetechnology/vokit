from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, replace

from control_plane.agents.application.index import sync_agent_index
from control_plane.agents.application.ports import (
    AgentIndexRepository,
    TemplateRecord,
    TemplateRepository,
    TemplateVersionRecord,
    TemplateVersionRepository,
)
from control_plane.agents.domain.policies import (
    assert_agent_type,
    assert_fallback,
    assert_no_secrets,
    assert_tools,
)
from control_plane.agents.domain.types import TemplateStatus, TemplateVisibility
from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.customers.domain.policies import customer_not_found
from control_plane.risk.application.gate import CustomerRiskGate
from control_plane.risk.domain.types import AgentStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.agents.domain import TenantAgent
from tenant.agents.service import TenantAgentService
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.agents")


@dataclass(frozen=True, slots=True)
class CreateTemplateCommand:
    name: str
    industry: str
    use_case: str
    description: str
    languages: str
    visibility: str
    selected_tenant_ids: tuple[uuid.UUID, ...]
    agent_type: str
    instructions: str
    voice_provider: str
    voice_id: str
    language: str
    tools: tuple[str, ...]
    fallback_behavior: str


class CreateTemplate:
    def __init__(
        self,
        templates: TemplateRepository,
        versions: TemplateVersionRepository,
        clock: Clock,
    ) -> None:
        self._templates = templates
        self._versions = versions
        self._clock = clock

    def execute(
        self, command: CreateTemplateCommand
    ) -> tuple[TemplateRecord, TemplateVersionRecord]:
        name = command.name.strip()
        if not name:
            raise DomainError("validation_error", "name is required.")
        try:
            visibility = TemplateVisibility(command.visibility.strip() or "global")
        except ValueError as exc:
            raise DomainError("validation_error", "visibility is invalid.") from exc
        assert_no_secrets(command.instructions, field="instructions")
        now = self._clock.now()
        template = TemplateRecord(
            id=new_uuid7(),
            name=name[:128],
            industry=command.industry.strip()[:64],
            use_case=command.use_case.strip()[:64],
            description=command.description.strip()[:255],
            languages=(command.languages.strip() or "en")[:128],
            visibility=visibility,
            selected_tenant_ids=command.selected_tenant_ids,
            status=TemplateStatus.ACTIVE,
            created_at=now,
        )
        version = TemplateVersionRecord(
            id=new_uuid7(),
            template_id=template.id,
            version=1,
            agent_type=assert_agent_type(command.agent_type),
            instructions=command.instructions,
            voice_provider=command.voice_provider.strip(),
            voice_id=command.voice_id.strip(),
            language=(command.language.strip() or "en")[:16],
            tools=assert_tools(command.tools),
            fallback_behavior=assert_fallback(command.fallback_behavior or "message"),
            used_at=None,
            created_at=now,
        )
        self._templates.create(template)
        self._versions.create(version)
        return template, version


class InstallTemplate:
    def __init__(
        self,
        templates: TemplateRepository,
        versions: TemplateVersionRepository,
        customers: CustomerIndexRepository,
        lifecycle: TenantLifecycleService,
        agents: TenantAgentService,
        gate: CustomerRiskGate,
        index: AgentIndexRepository,
        clock: Clock,
    ) -> None:
        self._templates = templates
        self._versions = versions
        self._customers = customers
        self._lifecycle = lifecycle
        self._agents = agents
        self._gate = gate
        self._index = index
        self._clock = clock

    def execute(
        self,
        *,
        template_id: uuid.UUID,
        customer_id: uuid.UUID,
        display_name: str,
        actor_tenant_id: uuid.UUID | None,
        privileged: bool,
    ) -> TenantAgent:
        template = self._templates.get(template_id)
        if template is None or template.status is TemplateStatus.ARCHIVED:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        customer = self._customers.get(customer_id)
        if customer is None:
            raise customer_not_found()
        if not privileged:
            if actor_tenant_id is None or actor_tenant_id != customer.tenant_id:
                raise customer_not_found()
        if not _visible_to(template, customer.tenant_id):
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if self._lifecycle.get_customer(customer.tenant_id, customer.id) is None:
            raise customer_not_found()
        self._gate.assert_open(customer.id)
        version = self._versions.latest(template.id)
        if version is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        now = self._clock.now()
        name = display_name.strip() or template.name
        agent = TenantAgent(
            agent_id=new_uuid7(),
            tenant_id=customer.tenant_id,
            customer_id=customer.id,
            display_name=name[:128],
            status=AgentStatus.DRAFT,
            created_at=now,
            updated_at=now,
            agent_type=version.agent_type,
            voice_provider=version.voice_provider,
            voice_id=version.voice_id,
            language=version.language,
            fallback_behavior=version.fallback_behavior,
            instructions="",
            template_instructions=version.instructions,
            tools=version.tools,
            template_id=template.id,
        )
        stored = self._agents.put_agent(customer.tenant_id, agent)
        if version.used_at is None:
            self._versions.update(replace(version, used_at=now))
        sync_agent_index(self._index, stored)
        log_event(
            logger,
            "agent.template.installed",
            outcome="success",
            tenant_id=str(customer.tenant_id),
            customer_id=str(customer.id),
            template_id=str(template.id),
            agent_id=str(stored.agent_id),
        )
        return stored


def _visible_to(template: TemplateRecord, tenant_id: uuid.UUID) -> bool:
    if template.visibility is TemplateVisibility.INTERNAL:
        return False
    if template.visibility is TemplateVisibility.GLOBAL:
        return True
    return tenant_id in template.selected_tenant_ids
