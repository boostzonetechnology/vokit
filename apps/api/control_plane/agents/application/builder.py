from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, replace

from control_plane.agents.application.index import sync_agent_index
from control_plane.agents.application.ports import (
    AgentIndexRepository,
    GlobalInstructionRepository,
)
from control_plane.agents.application.resolve import resolve_for_agent
from control_plane.agents.domain.policies import (
    assert_agent_type,
    assert_fallback,
    assert_no_secrets,
    assert_production_routable,
    assert_tools,
    publish_failures,
)
from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.risk.application.gate import CustomerRiskGate
from control_plane.risk.domain.types import AgentStatus
from control_plane.telephony.domain.destinations import parse_hours
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.agents.domain import AgentVersionRecord, TenantAgent, agent_snapshot
from tenant.agents.service import TenantAgentService
from tenant.billing.service import TenantBillingService
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.agents")


@dataclass(frozen=True, slots=True)
class ConfigureAgentCommand:
    agent_id: uuid.UUID
    actor_tenant_id: uuid.UUID | None
    privileged: bool
    display_name: str | None = None
    agent_type: str | None = None
    timezone: str | None = None
    voice_provider: str | None = None
    voice_id: str | None = None
    language: str | None = None
    greeting: str | None = None
    fallback_behavior: str | None = None
    inbound_enabled: bool | None = None
    outbound_enabled: bool | None = None
    recording_disclosure: bool | None = None
    instructions: str | None = None
    tools: tuple[str, ...] | None = None
    customer_can_edit: bool | None = None
    business_hours: tuple[dict[str, object], ...] | None = None
    voicemail_greeting: str | None = None
    outbound_voicemail_message: str | None = None
    default_transfer_id: uuid.UUID | None = None


class ConfigureAgent:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        agents: TenantAgentService,
        index: AgentIndexRepository,
        clock: Clock,
    ) -> None:
        self._customers = customers
        self._agents = agents
        self._index = index
        self._clock = clock

    def execute(self, command: ConfigureAgentCommand) -> TenantAgent:
        agent = _load_agent(
            self._agents, command.agent_id, command.actor_tenant_id, command.privileged
        )
        if agent.status is AgentStatus.SUSPENDED:
            raise DomainError(
                "agent_suspended",
                "Suspended agents cannot be edited.",
                http_status=409,
            )
        name = agent.display_name
        if command.display_name is not None:
            name = command.display_name.strip()
            if not name:
                raise DomainError("validation_error", "display_name is required.")
        agent_type = agent.agent_type
        if command.agent_type is not None:
            agent_type = assert_agent_type(command.agent_type)
        tools = agent.tools
        if command.tools is not None:
            tools = assert_tools(command.tools)
        fallback = agent.fallback_behavior
        if command.fallback_behavior is not None:
            fallback = assert_fallback(command.fallback_behavior)
        instructions = agent.instructions
        if command.instructions is not None:
            assert_no_secrets(command.instructions, field="instructions")
            instructions = command.instructions
        greeting = agent.greeting if command.greeting is None else command.greeting
        assert_no_secrets(greeting, field="greeting")
        vm_greeting = (
            agent.voicemail_greeting
            if command.voicemail_greeting is None
            else command.voicemail_greeting
        )
        assert_no_secrets(vm_greeting, field="voicemail_greeting")
        outbound_vm = (
            agent.outbound_voicemail_message
            if command.outbound_voicemail_message is None
            else command.outbound_voicemail_message
        )
        assert_no_secrets(outbound_vm, field="outbound_voicemail_message")
        hours = agent.business_hours
        if command.business_hours is not None:
            hours = tuple(
                {"weekday": item.weekday, "start": item.start, "end": item.end}
                for item in parse_hours(list(command.business_hours))
            )
        transfer_id = (
            agent.default_transfer_id
            if command.default_transfer_id is None
            else command.default_transfer_id
        )
        updated = replace(
            agent,
            display_name=name[:128],
            agent_type=agent_type,
            timezone=(command.timezone or agent.timezone or "UTC")[:64],
            voice_provider=agent.voice_provider
            if command.voice_provider is None
            else command.voice_provider.strip(),
            voice_id=agent.voice_id if command.voice_id is None else command.voice_id.strip(),
            language=agent.language if command.language is None else command.language.strip(),
            greeting=greeting,
            fallback_behavior=fallback,
            inbound_enabled=agent.inbound_enabled
            if command.inbound_enabled is None
            else command.inbound_enabled,
            outbound_enabled=agent.outbound_enabled
            if command.outbound_enabled is None
            else command.outbound_enabled,
            recording_disclosure=agent.recording_disclosure
            if command.recording_disclosure is None
            else command.recording_disclosure,
            instructions=instructions,
            tools=tools,
            customer_can_edit=agent.customer_can_edit
            if command.customer_can_edit is None
            else command.customer_can_edit,
            business_hours=hours,
            voicemail_greeting=vm_greeting,
            outbound_voicemail_message=outbound_vm,
            default_transfer_id=transfer_id,
            draft_version=agent.draft_version + 1,
            updated_at=self._clock.now(),
        )
        stored = self._agents.put_agent(agent.tenant_id, updated)
        sync_agent_index(self._index, stored)
        return stored


class PublishAgent:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        lifecycle: TenantLifecycleService,
        billing: TenantBillingService,
        agents: TenantAgentService,
        instructions: GlobalInstructionRepository,
        gate: CustomerRiskGate,
        index: AgentIndexRepository,
        clock: Clock,
    ) -> None:
        self._customers = customers
        self._lifecycle = lifecycle
        self._billing = billing
        self._agents = agents
        self._instructions = instructions
        self._gate = gate
        self._index = index
        self._clock = clock

    def execute(
        self, *, agent_id: uuid.UUID, actor_tenant_id: uuid.UUID | None, privileged: bool
    ) -> TenantAgent:
        agent = _load_agent(self._agents, agent_id, actor_tenant_id, privileged)
        self._gate.assert_open(agent.customer_id)
        customer = self._lifecycle.get_customer(agent.tenant_id, agent.customer_id)
        subscription = self._billing.get_active_subscription(agent.tenant_id, agent.customer_id)
        resolved = resolve_for_agent(agent, self._agents, self._instructions)
        failures = publish_failures(
            customer_status=customer.status if customer else None,
            has_subscription=subscription is not None,
            resolved_instructions=resolved,
            voice_provider=agent.voice_provider,
            voice_id=agent.voice_id,
            language=agent.language,
            recording_disclosure=agent.recording_disclosure,
            fallback_behavior=agent.fallback_behavior,
            status=agent.status,
        )
        if failures:
            raise DomainError(
                "publish_preflight_failed",
                "Agent is not ready to publish.",
                http_status=409,
                details={"failures": failures},
            )
        now = self._clock.now()
        version = agent.draft_version
        published = replace(
            agent,
            status=AgentStatus.ACTIVE,
            published_version=version,
            updated_at=now,
        )
        stored = self._agents.put_agent(agent.tenant_id, published)
        self._agents.put_version(
            agent.tenant_id,
            AgentVersionRecord(
                version_id=new_uuid7(),
                agent_id=agent.agent_id,
                tenant_id=agent.tenant_id,
                version=version,
                published=True,
                snapshot=agent_snapshot(stored),
                created_at=now,
            ),
        )
        sync_agent_index(self._index, stored)
        log_event(
            logger,
            "agent.published",
            outcome="success",
            tenant_id=str(agent.tenant_id),
            customer_id=str(agent.customer_id),
            agent_id=str(agent.agent_id),
            version=version,
        )
        return stored


class PauseAgent:
    def __init__(
        self, agents: TenantAgentService, index: AgentIndexRepository, clock: Clock
    ) -> None:
        self._agents = agents
        self._index = index
        self._clock = clock

    def execute(
        self, *, agent_id: uuid.UUID, actor_tenant_id: uuid.UUID | None, privileged: bool
    ) -> TenantAgent:
        agent = _load_agent(self._agents, agent_id, actor_tenant_id, privileged)
        if agent.status is AgentStatus.SUSPENDED:
            raise DomainError(
                "agent_suspended",
                "Suspended agents cannot be paused.",
                http_status=409,
            )
        stored = self._agents.put_agent(
            agent.tenant_id,
            replace(agent, status=AgentStatus.PAUSED, updated_at=self._clock.now()),
        )
        sync_agent_index(self._index, stored)
        log_event(
            logger,
            "agent.paused",
            outcome="success",
            tenant_id=str(agent.tenant_id),
            agent_id=str(agent.agent_id),
        )
        return stored


class CloneAgent:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        agents: TenantAgentService,
        gate: CustomerRiskGate,
        index: AgentIndexRepository,
        clock: Clock,
    ) -> None:
        self._customers = customers
        self._agents = agents
        self._gate = gate
        self._index = index
        self._clock = clock

    def execute(
        self, *, agent_id: uuid.UUID, actor_tenant_id: uuid.UUID | None, privileged: bool
    ) -> TenantAgent:
        source = _load_agent(self._agents, agent_id, actor_tenant_id, privileged)
        self._gate.assert_open(source.customer_id)
        now = self._clock.now()
        clone = replace(
            source,
            agent_id=new_uuid7(),
            display_name=f"{source.display_name} copy"[:128],
            status=AgentStatus.DRAFT,
            published_version=None,
            draft_version=1,
            created_at=now,
            updated_at=now,
        )
        stored = self._agents.put_agent(source.tenant_id, clone)
        sync_agent_index(self._index, stored)
        return stored


def _load_agent(
    agents: TenantAgentService,
    agent_id: uuid.UUID,
    actor_tenant_id: uuid.UUID | None,
    privileged: bool,
) -> TenantAgent:
    from control_plane.agents.infrastructure.repositories import DjangoAgentIndexRepository

    row = DjangoAgentIndexRepository().get(agent_id)
    if row is None:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    if not privileged:
        if actor_tenant_id is None or actor_tenant_id != row.tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
    agent = agents.get_agent(row.tenant_id, agent_id)
    if agent is None:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    return agent


def assert_agent_routable(
    agents: TenantAgentService,
    *,
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    production: bool = True,
) -> TenantAgent:
    agent = agents.get_agent(tenant_id, agent_id)
    if agent is None:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    if production:
        assert_production_routable(
            status=agent.status, published_version=agent.published_version
        )
    return agent
