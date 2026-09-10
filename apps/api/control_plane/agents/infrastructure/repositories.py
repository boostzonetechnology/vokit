from __future__ import annotations

import uuid

from control_plane.agents.application.ports import (
    AgentIndexRecord,
    TemplateRecord,
    TemplateVersionRecord,
)
from control_plane.agents.domain.types import TemplateStatus, TemplateVisibility
from control_plane.agents.models import (
    AgentIndex,
    AgentTemplate,
    GlobalInstruction,
    GlobalKnowledgeSource,
    TemplateVersion,
)
from control_plane.risk.domain.types import AgentStatus
from shared_kernel.ids import new_uuid7


def _template(row: AgentTemplate) -> TemplateRecord:
    selected = tuple(uuid.UUID(str(item)) for item in (row.selected_tenant_ids or []))
    return TemplateRecord(
        id=row.id,
        name=row.name,
        industry=row.industry,
        use_case=row.use_case,
        description=row.description,
        languages=row.languages,
        visibility=TemplateVisibility(row.visibility),
        selected_tenant_ids=selected,
        status=TemplateStatus(row.status),
        created_at=row.created_at,
    )


def _version(row: TemplateVersion) -> TemplateVersionRecord:
    tools = tuple(str(item) for item in (row.tools or []))
    return TemplateVersionRecord(
        id=row.id,
        template_id=row.template_id,
        version=row.version,
        agent_type=row.agent_type,
        instructions=row.instructions,
        voice_provider=row.voice_provider,
        voice_id=row.voice_id,
        language=row.language,
        tools=tools,
        fallback_behavior=row.fallback_behavior,
        used_at=row.used_at,
        created_at=row.created_at,
    )


class DjangoTemplateRepository:
    def create(self, record: TemplateRecord) -> None:
        AgentTemplate.objects.create(
            id=record.id,
            name=record.name,
            industry=record.industry,
            use_case=record.use_case,
            description=record.description,
            languages=record.languages,
            visibility=record.visibility.value,
            selected_tenant_ids=[str(item) for item in record.selected_tenant_ids],
            status=record.status.value,
        )

    def get(self, template_id: uuid.UUID) -> TemplateRecord | None:
        row = AgentTemplate.objects.filter(id=template_id).first()
        return _template(row) if row else None

    def list(self, *, status: TemplateStatus | None = None) -> list[TemplateRecord]:
        rows = AgentTemplate.objects.order_by("created_at")
        if status is not None:
            rows = rows.filter(status=status.value)
        return [_template(row) for row in rows]

    def update(self, record: TemplateRecord) -> None:
        AgentTemplate.objects.filter(id=record.id).update(
            name=record.name,
            industry=record.industry,
            use_case=record.use_case,
            description=record.description,
            languages=record.languages,
            visibility=record.visibility.value,
            selected_tenant_ids=[str(item) for item in record.selected_tenant_ids],
            status=record.status.value,
        )


class DjangoTemplateVersionRepository:
    def create(self, record: TemplateVersionRecord) -> None:
        TemplateVersion.objects.create(
            id=record.id,
            template_id=record.template_id,
            version=record.version,
            agent_type=record.agent_type,
            instructions=record.instructions,
            voice_provider=record.voice_provider,
            voice_id=record.voice_id,
            language=record.language,
            tools=list(record.tools),
            fallback_behavior=record.fallback_behavior,
            used_at=record.used_at,
        )

    def get(self, version_id: uuid.UUID) -> TemplateVersionRecord | None:
        row = TemplateVersion.objects.filter(id=version_id).first()
        return _version(row) if row else None

    def latest(self, template_id: uuid.UUID) -> TemplateVersionRecord | None:
        row = (
            TemplateVersion.objects.filter(template_id=template_id)
            .order_by("-version")
            .first()
        )
        return _version(row) if row else None

    def list_for_template(self, template_id: uuid.UUID) -> list[TemplateVersionRecord]:
        rows = TemplateVersion.objects.filter(template_id=template_id).order_by("version")
        return [_version(row) for row in rows]

    def update(self, record: TemplateVersionRecord) -> None:
        TemplateVersion.objects.filter(id=record.id).update(used_at=record.used_at)

    def next_version(self, template_id: uuid.UUID) -> int:
        latest = self.latest(template_id)
        return 1 if latest is None else latest.version + 1


class DjangoGlobalInstructionRepository:
    def get(self) -> str:
        row = GlobalInstruction.objects.order_by("-version").first()
        return row.body if row else ""

    def save(self, body: str) -> str:
        latest = GlobalInstruction.objects.order_by("-version").first()
        version = 1 if latest is None else latest.version + 1
        GlobalInstruction.objects.create(id=new_uuid7(), body=body, version=version)
        return body


class DjangoGlobalKnowledgeRepository:
    def create(self, source_id: uuid.UUID, title: str, body: str) -> None:
        GlobalKnowledgeSource.objects.create(
            id=source_id, title=title, body=body, status="ready", group_id="global"
        )

    def get(self, source_id: uuid.UUID) -> tuple[uuid.UUID, str, str] | None:
        row = GlobalKnowledgeSource.objects.filter(id=source_id).first()
        if row is None:
            return None
        return (row.id, row.title, row.body)

    def list(self) -> list[tuple[uuid.UUID, str, str]]:
        return [(row.id, row.title, row.body) for row in GlobalKnowledgeSource.objects.all()]


class DjangoAgentIndexRepository:
    def upsert(self, record: AgentIndexRecord) -> None:
        AgentIndex.objects.update_or_create(
            id=record.id,
            defaults={
                "tenant_id": record.tenant_id,
                "customer_id": record.customer_id,
                "display_name": record.display_name,
                "status": record.status.value,
                "agent_type": record.agent_type,
                "published_version": record.published_version,
            },
        )

    def get(self, agent_id: uuid.UUID) -> AgentIndexRecord | None:
        row = AgentIndex.objects.filter(id=agent_id).first()
        if row is None:
            return None
        return AgentIndexRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            display_name=row.display_name,
            status=AgentStatus(row.status),
            agent_type=row.agent_type,
            published_version=row.published_version,
            created_at=row.created_at,
        )

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
        status: AgentStatus | None = None,
    ) -> list[AgentIndexRecord]:
        rows = AgentIndex.objects.order_by("created_at")
        if tenant_id is not None:
            rows = rows.filter(tenant_id=tenant_id)
        if customer_id is not None:
            rows = rows.filter(customer_id=customer_id)
        if status is not None:
            rows = rows.filter(status=status.value)
        return [
            AgentIndexRecord(
                id=row.id,
                tenant_id=row.tenant_id,
                customer_id=row.customer_id,
                display_name=row.display_name,
                status=AgentStatus(row.status),
                agent_type=row.agent_type,
                published_version=row.published_version,
                created_at=row.created_at,
            )
            for row in rows
        ]
