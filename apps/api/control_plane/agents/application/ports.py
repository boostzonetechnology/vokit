from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.agents.domain.types import TemplateStatus, TemplateVisibility
from control_plane.risk.domain.types import AgentStatus


@dataclass(frozen=True, slots=True)
class TemplateRecord:
    id: uuid.UUID
    name: str
    industry: str
    use_case: str
    description: str
    languages: str
    visibility: TemplateVisibility
    selected_tenant_ids: tuple[uuid.UUID, ...]
    status: TemplateStatus
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TemplateVersionRecord:
    id: uuid.UUID
    template_id: uuid.UUID
    version: int
    agent_type: str
    instructions: str
    voice_provider: str
    voice_id: str
    language: str
    tools: tuple[str, ...]
    fallback_behavior: str
    used_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AgentIndexRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    display_name: str
    status: AgentStatus
    agent_type: str
    published_version: int | None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class KnowledgePoint:
    point_id: str
    vector: list[float]
    group_id: str
    tenant_id: str
    customer_id: str
    agent_id: str
    source_id: str
    document_id: str
    chunk_id: str
    text: str
    speak_text: str
    is_active: bool = True


class TemplateRepository(Protocol):
    def create(self, record: TemplateRecord) -> None: ...

    def get(self, template_id: uuid.UUID) -> TemplateRecord | None: ...

    def list(self, *, status: TemplateStatus | None = None) -> list[TemplateRecord]: ...

    def update(self, record: TemplateRecord) -> None: ...


class TemplateVersionRepository(Protocol):
    def create(self, record: TemplateVersionRecord) -> None: ...

    def get(self, version_id: uuid.UUID) -> TemplateVersionRecord | None: ...

    def latest(self, template_id: uuid.UUID) -> TemplateVersionRecord | None: ...

    def list_for_template(self, template_id: uuid.UUID) -> list[TemplateVersionRecord]: ...

    def update(self, record: TemplateVersionRecord) -> None: ...

    def next_version(self, template_id: uuid.UUID) -> int: ...


class GlobalInstructionRepository(Protocol):
    def get(self) -> str: ...

    def save(self, body: str) -> str: ...


class GlobalKnowledgeRepository(Protocol):
    def create(self, source_id: uuid.UUID, title: str, body: str) -> None: ...

    def get(self, source_id: uuid.UUID) -> tuple[uuid.UUID, str, str] | None: ...

    def list(self) -> list[tuple[uuid.UUID, str, str]]: ...


class AgentIndexRepository(Protocol):
    def upsert(self, record: AgentIndexRecord) -> None: ...

    def get(self, agent_id: uuid.UUID) -> AgentIndexRecord | None: ...

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
        status: AgentStatus | None = None,
    ) -> list[AgentIndexRecord]: ...


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]: ...


class KnowledgeVectorStore(Protocol):
    def upsert(self, points: list[KnowledgePoint]) -> None: ...

    def delete_source(self, source_id: str) -> None: ...

    def search(self, group_ids: list[str], vector: list[float], top_k: int = 5) -> list[dict]: ...
