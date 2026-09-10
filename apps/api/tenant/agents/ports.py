from __future__ import annotations

import uuid
from typing import Protocol

from tenant.agents.domain import (
    AgentVersionRecord,
    InstructionLayerRecord,
    KnowledgeAttachmentRecord,
    KnowledgeSourceRecord,
    TenantAgent,
    TestSessionRecord,
)
from tenant.runtime.ports import TenantConnection


class TenantAgentStore(Protocol):
    def put_agent(self, connection: TenantConnection, agent: TenantAgent) -> None: ...

    def get_agent(
        self, connection: TenantConnection, agent_id: uuid.UUID
    ) -> TenantAgent | None: ...

    def list_agents(
        self,
        connection: TenantConnection,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantAgent]: ...

    def put_version(self, connection: TenantConnection, row: AgentVersionRecord) -> None: ...

    def list_versions(
        self, connection: TenantConnection, agent_id: uuid.UUID
    ) -> list[AgentVersionRecord]: ...

    def put_instruction(
        self, connection: TenantConnection, row: InstructionLayerRecord
    ) -> None: ...

    def get_instruction(
        self, connection: TenantConnection, scope: str, owner_id: uuid.UUID
    ) -> InstructionLayerRecord | None: ...

    def put_knowledge(self, connection: TenantConnection, row: KnowledgeSourceRecord) -> None: ...

    def get_knowledge(
        self, connection: TenantConnection, source_id: uuid.UUID
    ) -> KnowledgeSourceRecord | None: ...

    def list_knowledge(
        self, connection: TenantConnection, *, scope: str | None = None
    ) -> list[KnowledgeSourceRecord]: ...

    def put_attachment(
        self, connection: TenantConnection, row: KnowledgeAttachmentRecord
    ) -> None: ...

    def list_attachments(
        self, connection: TenantConnection, agent_id: uuid.UUID
    ) -> list[KnowledgeAttachmentRecord]: ...

    def delete_attachment(
        self, connection: TenantConnection, agent_id: uuid.UUID, source_id: uuid.UUID
    ) -> None: ...

    def put_session(self, connection: TenantConnection, row: TestSessionRecord) -> None: ...

    def get_session(
        self, connection: TenantConnection, session_id: uuid.UUID
    ) -> TestSessionRecord | None: ...
