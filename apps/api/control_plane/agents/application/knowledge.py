from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from control_plane.agents.application.builder import _load_agent
from control_plane.agents.application.ports import (
    EmbeddingProvider,
    GlobalKnowledgeRecord,
    GlobalKnowledgeRepository,
    KnowledgeJobQueue,
    KnowledgePoint,
    KnowledgeVectorStore,
)
from control_plane.agents.domain.policies import (
    assert_knowledge_attach_scope,
    assert_no_secrets,
    chunk_text,
    knowledge_checksum,
    knowledge_group_id,
    knowledge_in_use,
)
from control_plane.agents.domain.types import KnowledgeKind, KnowledgeScope, KnowledgeStatus
from control_plane.audit.application.record import RecordAuditCommand
from control_plane.audit.infrastructure.container import record_audit
from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.http.correlation import get_correlation_id
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
    filename: str = ""
    content_type: str = ""
    file_bytes: bytes | None = None


class IngestKnowledge:
    def __init__(
        self,
        agents: TenantAgentService,
        globals_: GlobalKnowledgeRepository,
        clock: Clock,
        customers: CustomerIndexRepository,
        jobs: KnowledgeJobQueue,
        extract: Callable[..., str],
    ) -> None:
        self._agents = agents
        self._globals = globals_
        self._clock = clock
        self._customers = customers
        self._jobs = jobs
        self._extract = extract

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
        title = command.title.strip() or (command.filename or "").rsplit("/", 1)[-1]
        title = title.rsplit("\\", 1)[-1].strip()
        if not title:
            raise DomainError("validation_error", "title is required.")
        if command.file_bytes is not None:
            kind = KnowledgeKind.FILE
            body = self._extract(
                filename=command.filename or command.object_ref,
                content_type=command.content_type,
                data=command.file_bytes,
            )
            object_ref = (command.filename or command.object_ref or title)[:128]
        else:
            if kind in {KnowledgeKind.URL, KnowledgeKind.FILE} and not command.body.strip():
                raise DomainError(
                    "knowledge_ingest_failed",
                    "URL/file ingest requires a file upload or extracted text; "
                    "remote fetch is disabled.",
                    http_status=422,
                )
            body = command.body.strip()
            object_ref = command.object_ref.strip()[:128]
        if not body:
            raise DomainError("validation_error", "body is required.")
        assert_no_secrets(body, field="knowledge")
        owner_id = _assert_owner(
            command,
            scope=scope,
            agents=self._agents,
            customers=self._customers,
        )
        source_id = new_uuid7()
        group_id = knowledge_group_id(
            scope,
            tenant_id=str(command.tenant_id) if scope is not KnowledgeScope.GLOBAL else "",
            customer_id=str(owner_id) if scope is KnowledgeScope.CUSTOMER else "",
            agent_id=str(owner_id) if scope is KnowledgeScope.AGENT else "",
        )
        now = self._clock.now()
        checksum = knowledge_checksum(body)
        if scope is KnowledgeScope.GLOBAL:
            self._globals.create(
                GlobalKnowledgeRecord(
                    source_id=source_id,
                    title=title[:128],
                    body=body,
                    status=KnowledgeStatus.QUEUED.value,
                    kind=kind.value,
                    object_ref=object_ref,
                    checksum=checksum,
                    group_id="global",
                )
            )
            tenant_id = None
        else:
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
                    object_ref=object_ref,
                    checksum=checksum,
                    status=KnowledgeStatus.QUEUED.value,
                    group_id=group_id,
                    customer_can_edit=command.customer_can_edit,
                    created_at=now,
                    updated_at=now,
                ),
            )
            tenant_id = command.tenant_id
        self._jobs.enqueue_process(
            source_id=source_id,
            tenant_id=tenant_id,
            correlation_id=get_correlation_id() or "",
        )
        stored_status, stored_group = _current_status(
            source_id,
            tenant_id=tenant_id,
            agents=self._agents,
            globals_=self._globals,
            fallback_group=group_id,
        )
        log_event(
            logger,
            "knowledge.queued",
            outcome="success",
            tenant_id=str(command.tenant_id) if scope is not KnowledgeScope.GLOBAL else None,
            source_id=str(source_id),
            scope=scope.value,
            status=stored_status,
        )
        return {
            "id": str(source_id),
            "title": title[:128],
            "scope": scope.value,
            "kind": kind.value,
            "status": stored_status,
            "group_id": stored_group,
        }


class ProcessKnowledge:
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

    def execute(self, *, source_id: uuid.UUID, tenant_id: uuid.UUID | None) -> dict:
        source = _load_source(self._agents, self._globals, source_id, tenant_id)
        if source.status == KnowledgeStatus.READY.value:
            return {"id": str(source_id), "status": source.status, "chunks": 0}
        processing = _with_status(source, KnowledgeStatus.PROCESSING.value, self._clock.now())
        _save_source(self._agents, self._globals, processing)
        chunks = chunk_text(source.body)
        if not chunks:
            failed = _with_status(processing, KnowledgeStatus.FAILED.value, self._clock.now())
            _save_source(self._agents, self._globals, failed)
            return {
                "id": str(source_id),
                "status": KnowledgeStatus.FAILED.value,
                "chunks": 0,
                "error": "knowledge_extract_failed",
            }
        points = [
            KnowledgePoint(
                point_id=str(new_uuid7()),
                vector=self._embeddings.embed(chunk),
                group_id=source.group_id,
                tenant_id=str(source.tenant_id) if source.tenant_id else "",
                customer_id=str(source.owner_id)
                if source.scope == KnowledgeScope.CUSTOMER.value
                else "",
                agent_id=str(source.owner_id) if source.scope == KnowledgeScope.AGENT.value else "",
                source_id=str(source.source_id),
                document_id=str(source.source_id),
                chunk_id=str(index),
                text=chunk,
                speak_text=chunk[:240],
            )
            for index, chunk in enumerate(chunks)
        ]
        try:
            self._vectors.upsert(points)
        except DomainError as exc:
            failed = _with_status(processing, KnowledgeStatus.FAILED.value, self._clock.now())
            _save_source(self._agents, self._globals, failed)
            log_event(
                logger,
                "knowledge.ingest.failed",
                outcome="failure",
                source_id=str(source_id),
                tenant_id=str(tenant_id) if tenant_id else None,
                error=exc.code,
            )
            return {
                "id": str(source_id),
                "status": KnowledgeStatus.FAILED.value,
                "chunks": 0,
                "error": exc.code,
            }
        ready = _with_status(processing, KnowledgeStatus.READY.value, self._clock.now())
        _save_source(self._agents, self._globals, ready)
        log_event(
            logger,
            "knowledge.ingested",
            outcome="success",
            tenant_id=str(tenant_id) if tenant_id else None,
            source_id=str(source_id),
            scope=source.scope,
            chunks=len(points),
        )
        return {"id": str(source_id), "status": KnowledgeStatus.READY.value, "chunks": len(points)}


class AttachKnowledge:
    def __init__(
        self, agents: TenantAgentService, globals_: GlobalKnowledgeRepository
    ) -> None:
        self._agents = agents
        self._globals = globals_

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
        global_row = self._globals.get(source_id)
        if global_group or global_row is not None:
            if global_row is None:
                raise DomainError("not_found", "Resource not found.", http_status=404)
            if global_row.status != KnowledgeStatus.READY.value:
                raise DomainError(
                    "knowledge_not_ready",
                    "Knowledge source is not ready to attach.",
                    http_status=409,
                )
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
        assert_knowledge_attach_scope(agent=agent, source=source)
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


class DetachKnowledge:
    def __init__(self, agents: TenantAgentService) -> None:
        self._agents = agents

    def execute(
        self,
        *,
        agent_id: uuid.UUID,
        source_id: uuid.UUID,
        actor_tenant_id: uuid.UUID | None,
        privileged: bool,
    ) -> None:
        agent = _load_agent(self._agents, agent_id, actor_tenant_id, privileged)
        attached = {
            row.source_id
            for row in self._agents.list_attachments(agent.tenant_id, agent.agent_id)
        }
        if source_id not in attached:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        self._agents.delete_attachment(agent.tenant_id, agent.agent_id, source_id)


class DeleteKnowledge:
    def __init__(
        self,
        agents: TenantAgentService,
        vectors: KnowledgeVectorStore,
        globals_: GlobalKnowledgeRepository,
    ) -> None:
        self._agents = agents
        self._vectors = vectors
        self._globals = globals_

    def execute(
        self,
        *,
        source_id: uuid.UUID,
        actor_tenant_id: uuid.UUID | None,
        privileged: bool,
        confirm: bool,
        actor_id=None,
        actor_role: str = "",
    ) -> dict:
        if privileged:
            global_row = self._globals.get(source_id)
            if global_row is not None:
                if not confirm:
                    raise knowledge_in_use([])
                self._vectors.delete_source(str(source_id))
                self._globals.delete(source_id)
                _audit_deleted(source_id, tenant_id=None, actor_id=actor_id, actor_role=actor_role)
                return {"deleted": True, "detached_agent_ids": []}
        if actor_tenant_id is None and not privileged:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        tenant_id = actor_tenant_id
        if tenant_id is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        source = self._agents.get_knowledge(tenant_id, source_id)
        if source is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        attachments = self._agents.list_attachments_for_source(tenant_id, source_id)
        agent_ids = [str(row.agent_id) for row in attachments]
        if attachments and not confirm:
            raise knowledge_in_use(agent_ids)
        self._agents.delete_attachments_for_source(tenant_id, source_id)
        self._vectors.delete_source(str(source_id))
        self._agents.delete_knowledge(tenant_id, source_id)
        _audit_deleted(
            source_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_role=actor_role,
            payload={"detached_agent_ids": agent_ids},
        )
        log_event(
            logger,
            "knowledge.deleted",
            outcome="success",
            tenant_id=str(tenant_id),
            source_id=str(source_id),
            detached=len(agent_ids),
        )
        return {"deleted": True, "detached_agent_ids": agent_ids}


def source_impact(
    agents: TenantAgentService, tenant_id: uuid.UUID, source_id: uuid.UUID
) -> dict[str, object]:
    source = agents.get_knowledge(tenant_id, source_id)
    if source is None:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    attachments = agents.list_attachments_for_source(tenant_id, source_id)
    return {
        "id": str(source.source_id),
        "title": source.title,
        "scope": source.scope,
        "kind": source.kind,
        "status": source.status,
        "group_id": source.group_id,
        "attached_agent_ids": [str(row.agent_id) for row in attachments],
        "attached_count": len(attachments),
    }


def _assert_owner(
    command: IngestKnowledgeCommand,
    *,
    scope: KnowledgeScope,
    agents: TenantAgentService,
    customers: CustomerIndexRepository,
) -> uuid.UUID:
    if scope is KnowledgeScope.GLOBAL:
        return command.owner_id
    if scope is KnowledgeScope.AGENCY:
        return command.tenant_id
    if scope is KnowledgeScope.CUSTOMER:
        customer = customers.get(command.owner_id)
        if customer is None or customer.tenant_id != command.tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return customer.id
    agent = agents.get_agent(command.tenant_id, command.owner_id)
    if agent is None:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    return agent.agent_id


def _current_status(
    source_id: uuid.UUID,
    *,
    tenant_id: uuid.UUID | None,
    agents: TenantAgentService,
    globals_: GlobalKnowledgeRepository,
    fallback_group: str,
) -> tuple[str, str]:
    if tenant_id is None:
        row = globals_.get(source_id)
        if row is None:
            return KnowledgeStatus.QUEUED.value, fallback_group
        return row.status, row.group_id
    row = agents.get_knowledge(tenant_id, source_id)
    if row is None:
        return KnowledgeStatus.QUEUED.value, fallback_group
    return row.status, row.group_id


class _LoadedSource:
    def __init__(
        self,
        *,
        source_id: uuid.UUID,
        tenant_id: uuid.UUID | None,
        scope: str,
        owner_id: uuid.UUID,
        body: str,
        status: str,
        group_id: str,
        title: str,
        kind: str,
        object_ref: str,
        checksum: str,
        customer_can_edit: bool = False,
        created_at=None,
    ) -> None:
        self.source_id = source_id
        self.tenant_id = tenant_id
        self.scope = scope
        self.owner_id = owner_id
        self.body = body
        self.status = status
        self.group_id = group_id
        self.title = title
        self.kind = kind
        self.object_ref = object_ref
        self.checksum = checksum
        self.customer_can_edit = customer_can_edit
        self.created_at = created_at


def _load_source(
    agents: TenantAgentService,
    globals_: GlobalKnowledgeRepository,
    source_id: uuid.UUID,
    tenant_id: uuid.UUID | None,
) -> _LoadedSource:
    if tenant_id is None:
        row = globals_.get(source_id)
        if row is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return _LoadedSource(
            source_id=row.source_id,
            tenant_id=None,
            scope=KnowledgeScope.GLOBAL.value,
            owner_id=row.source_id,
            body=row.body,
            status=row.status,
            group_id=row.group_id,
            title=row.title,
            kind=row.kind,
            object_ref=row.object_ref,
            checksum=row.checksum,
        )
    row = agents.get_knowledge(tenant_id, source_id)
    if row is None:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    return _LoadedSource(
        source_id=row.source_id,
        tenant_id=row.tenant_id,
        scope=row.scope,
        owner_id=row.owner_id,
        body=row.body,
        status=row.status,
        group_id=row.group_id,
        title=row.title,
        kind=row.kind,
        object_ref=row.object_ref,
        checksum=row.checksum,
        customer_can_edit=row.customer_can_edit,
        created_at=row.created_at,
    )


def _with_status(source: _LoadedSource, status: str, now) -> _LoadedSource:
    source.status = status
    source.created_at = source.created_at or now
    source._updated_at = now  # type: ignore[attr-defined]
    return source


def _save_source(
    agents: TenantAgentService,
    globals_: GlobalKnowledgeRepository,
    source: _LoadedSource,
) -> None:
    now = getattr(source, "_updated_at", None)
    if source.tenant_id is None:
        globals_.save(
            GlobalKnowledgeRecord(
                source_id=source.source_id,
                title=source.title,
                body=source.body,
                status=source.status,
                kind=source.kind,
                object_ref=source.object_ref,
                checksum=source.checksum,
                group_id=source.group_id,
            )
        )
        return
    agents.put_knowledge(
        source.tenant_id,
        KnowledgeSourceRecord(
            source_id=source.source_id,
            tenant_id=source.tenant_id,
            scope=source.scope,
            owner_id=source.owner_id,
            kind=source.kind,
            title=source.title,
            body=source.body,
            object_ref=source.object_ref,
            checksum=source.checksum,
            status=source.status,
            group_id=source.group_id,
            customer_can_edit=source.customer_can_edit,
            created_at=source.created_at,
            updated_at=now,
        ),
    )


def _audit_deleted(
    source_id: uuid.UUID,
    *,
    tenant_id,
    actor_id=None,
    actor_role: str = "",
    payload: dict | None = None,
) -> None:
    record_audit().execute(
        RecordAuditCommand(
            action="knowledge.deleted",
            entity_type="knowledge_source",
            entity_id=str(source_id),
            actor_id=actor_id,
            actor_role=actor_role,
            tenant_id=tenant_id,
            after_summary="deleted",
            payload=payload,
        )
    )
