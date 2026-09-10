from __future__ import annotations

import uuid
from dataclasses import replace

from control_plane.risk.domain.types import AgentStatus
from shared_kernel.errors import DomainError
from tenant.agents.domain import (
    AgentVersionRecord,
    InstructionLayerRecord,
    KnowledgeAttachmentRecord,
    KnowledgeSourceRecord,
    TenantAgent,
    TestSessionRecord,
)
from tenant.agents.ports import TenantAgentStore
from tenant.runtime.router import TenantRouter


class TenantAgentService:
    def __init__(self, router: TenantRouter, store: TenantAgentStore) -> None:
        self._router = router
        self._store = store

    def put_agent(self, tenant_id: uuid.UUID, agent: TenantAgent) -> TenantAgent:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_agent(connection, agent)
            stored = self._store.get_agent(connection, agent.agent_id)
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def get_agent(self, tenant_id: uuid.UUID, agent_id: uuid.UUID) -> TenantAgent | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_agent(connection, agent_id)

    def list_agents(
        self, tenant_id: uuid.UUID, customer_id: uuid.UUID | None = None
    ) -> list[TenantAgent]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_agents(connection, customer_id)

    def suspend_for_customer(
        self, tenant_id: uuid.UUID, customer_id: uuid.UUID, now
    ) -> list[TenantAgent]:
        updated: list[TenantAgent] = []
        with self._router.connection_for_tenant(tenant_id) as connection:
            for agent in self._store.list_agents(connection, customer_id):
                if agent.status is AgentStatus.SUSPENDED:
                    updated.append(agent)
                    continue
                suspended = replace(agent, status=AgentStatus.SUSPENDED, updated_at=now)
                self._store.put_agent(connection, suspended)
                stored = self._store.get_agent(connection, agent.agent_id)
                if stored is None:
                    raise DomainError(
                        "tenant_write_failed",
                        "Tenant write could not be verified.",
                        http_status=503,
                    )
                updated.append(stored)
        return updated

    def put_version(self, tenant_id: uuid.UUID, row: AgentVersionRecord) -> None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_version(connection, row)

    def list_versions(self, tenant_id: uuid.UUID, agent_id: uuid.UUID) -> list[AgentVersionRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_versions(connection, agent_id)

    def put_instruction(self, tenant_id: uuid.UUID, row: InstructionLayerRecord) -> None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_instruction(connection, row)

    def get_instruction(
        self, tenant_id: uuid.UUID, scope: str, owner_id: uuid.UUID
    ) -> InstructionLayerRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_instruction(connection, scope, owner_id)

    def put_knowledge(
        self, tenant_id: uuid.UUID, row: KnowledgeSourceRecord
    ) -> KnowledgeSourceRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_knowledge(connection, row)
            stored = self._store.get_knowledge(connection, row.source_id)
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def get_knowledge(
        self, tenant_id: uuid.UUID, source_id: uuid.UUID
    ) -> KnowledgeSourceRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_knowledge(connection, source_id)

    def list_knowledge(
        self, tenant_id: uuid.UUID, *, scope: str | None = None
    ) -> list[KnowledgeSourceRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_knowledge(connection, scope=scope)

    def put_attachment(self, tenant_id: uuid.UUID, row: KnowledgeAttachmentRecord) -> None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_attachment(connection, row)

    def list_attachments(
        self, tenant_id: uuid.UUID, agent_id: uuid.UUID
    ) -> list[KnowledgeAttachmentRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_attachments(connection, agent_id)

    def delete_attachment(
        self, tenant_id: uuid.UUID, agent_id: uuid.UUID, source_id: uuid.UUID
    ) -> None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.delete_attachment(connection, agent_id, source_id)

    def put_session(self, tenant_id: uuid.UUID, row: TestSessionRecord) -> TestSessionRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_session(connection, row)
            stored = self._store.get_session(connection, row.session_id)
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def get_session(
        self, tenant_id: uuid.UUID, session_id: uuid.UUID
    ) -> TestSessionRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_session(connection, session_id)
