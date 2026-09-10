from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.agents.application.builder import _load_agent
from control_plane.agents.application.ports import (
    EmbeddingProvider,
    GlobalKnowledgeRepository,
    KnowledgePoint,
    KnowledgeVectorStore,
)
from control_plane.agents.domain.policies import (
    assert_no_secrets,
    chunk_text,
    knowledge_group_id,
)
from control_plane.agents.domain.types import KnowledgeKind, KnowledgeScope, KnowledgeStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.agents.domain import KnowledgeAttachmentRecord, KnowledgeSourceRecord
from tenant.agents.service import TenantAgentService

logger = logging.getLogger("vokit.agents")


@dataclass(frozen=True, slots=True)
class IngestKnowledgeCommand:
    tenant_id: uuid.UUID
    scope: str
    owner_id: uuid.UUID
    title: str
    body: str
    kind: str = "text"
    object_ref: str = ""
    privileged: bool = False
    actor_tenant_id: uuid.UUID | None = None
    customer_can_edit: bool = False


class IngestKnowledge:
    def __init__(
        self,
        agents: TenantAgentService,
        vectors: KnowledgeVectorStore,
        embeddings: EmbeddingProvider,
        globals_: GlobalKnowledgeRepository,
        clock: Clock,
    ) -> None:
        self._agents = agents
        self._vectors = vectors
        self._embeddings = embeddings
        self._globals = globals_
        self._clock = clock

    def execute(self, command: IngestKnowledgeCommand) -> dict:
        try:
            scope = KnowledgeScope(command.scope)
            kind = KnowledgeKind(command.kind)
        except ValueError as exc:
            raise DomainError("validation_error", "scope or kind is invalid.") from exc
        if not command.privileged:
            if command.actor_tenant_id is None or command.actor_tenant_id != command.tenant_id:
                raise DomainError("not_found", "Resource not found.", http_status=404)
            if scope is KnowledgeScope.GLOBAL:
                raise DomainError("forbidden", "Not permitted.", http_status=403)
        title = command.title.strip()
        if not title:
            raise DomainError("validation_error", "title is required.")
        assert_no_secrets(command.body, field="knowledge")
        if kind in {KnowledgeKind.URL, KnowledgeKind.FILE} and not command.body.strip():
            raise DomainError(
                "knowledge_ingest_failed",
                "URL/file ingest requires extracted text; remote fetch is disabled.",
                http_status=422,
            )
        body = command.body.strip()
        if not body:
            raise DomainError("validation_error", "body is required.")
        source_id = new_uuid7()
        group_id = knowledge_group_id(
            scope,
            tenant_id=str(command.tenant_id) if scope is not KnowledgeScope.GLOBAL else "",
            customer_id=str(command.owner_id) if scope is KnowledgeScope.CUSTOMER else "",
            agent_id=str(command.owner_id) if scope is KnowledgeScope.AGENT else "",
        )
        now = self._clock.now()
        if scope is KnowledgeScope.GLOBAL:
            self._globals.create(source_id, title[:128], body)
        else:
            owner_id = command.owner_id
            if scope is KnowledgeScope.AGENCY:
                owner_id = command.tenant_id
            self._agents.put_knowledge(
                command.tenant_id,
                KnowledgeSourceRecord(
                    source_id=source_id,
                    tenant_id=command.tenant_id,
                    scope=scope.value,
                    owner_id=owner_id,
                    kind=kind.value,
                    title=title[:128],
                    body=body,
                    object_ref=command.object_ref.strip()[:128],
                    checksum="",
                    status=KnowledgeStatus.READY.value,
                    group_id=group_id,
                    customer_can_edit=command.customer_can_edit,
                    created_at=now,
                    updated_at=now,
                ),
            )
        points = []
        for index, chunk in enumerate(chunk_text(body)):
            points.append(
                KnowledgePoint(
                    point_id=str(new_uuid7()),
                    vector=self._embeddings.embed(chunk),
                    group_id=group_id,
                    tenant_id=str(command.tenant_id) if scope is not KnowledgeScope.GLOBAL else "",
                    customer_id=str(command.owner_id)
                    if scope is KnowledgeScope.CUSTOMER
                    else "",
                    agent_id=str(command.owner_id) if scope is KnowledgeScope.AGENT else "",
                    source_id=str(source_id),
                    document_id=str(source_id),
                    chunk_id=str(index),
                    text=chunk,
                    speak_text=chunk[:240],
                )
            )
        self._vectors.upsert(points)
        log_event(
            logger,
            "knowledge.ingested",
            outcome="success",
            tenant_id=str(command.tenant_id) if scope is not KnowledgeScope.GLOBAL else None,
            source_id=str(source_id),
            scope=scope.value,
            chunks=len(points),
        )
        return {
            "id": str(source_id),
            "title": title[:128],
            "scope": scope.value,
            "status": KnowledgeStatus.READY.value,
            "group_id": group_id,
            "chunks": len(points),
        }


class AttachKnowledge:
    def __init__(self, agents: TenantAgentService) -> None:
        self._agents = agents

    def execute(
        self,
        *,
        agent_id: uuid.UUID,
        source_id: uuid.UUID,
        actor_tenant_id: uuid.UUID | None,
        privileged: bool,
        global_group: bool = False,
    ) -> None:
        agent = _load_agent(self._agents, agent_id, actor_tenant_id, privileged)
        if global_group:
            self._agents.put_attachment(
                agent.tenant_id,
                KnowledgeAttachmentRecord(
                    agent_id=agent.agent_id,
                    source_id=source_id,
                    tenant_id=agent.tenant_id,
                    scope=KnowledgeScope.GLOBAL.value,
                    group_id="global",
                ),
            )
            return
        source = self._agents.get_knowledge(agent.tenant_id, source_id)
        if source is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        self._agents.put_attachment(
            agent.tenant_id,
            KnowledgeAttachmentRecord(
                agent_id=agent.agent_id,
                source_id=source.source_id,
                tenant_id=agent.tenant_id,
                scope=source.scope,
                group_id=source.group_id,
            ),
        )
