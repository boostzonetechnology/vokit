from __future__ import annotations

import logging
import uuid
from dataclasses import replace

from control_plane.agents.application.builder import _load_agent
from control_plane.agents.application.ports import (
    EmbeddingProvider,
    GlobalInstructionRepository,
    KnowledgeVectorStore,
)
from control_plane.agents.application.resolve import resolve_for_agent
from control_plane.agents.domain.policies import assert_test_routable
from control_plane.agents.domain.types import TestSessionKind, TestSessionStatus
from control_plane.risk.domain.types import AgentStatus
from control_plane.telephony.application.session import TrainingSessionIndexRepository
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.agents.domain import TestSessionRecord
from tenant.agents.service import TenantAgentService

logger = logging.getLogger("vokit.agents")


class StartTestSession:
    def __init__(
        self,
        agents: TenantAgentService,
        instructions: GlobalInstructionRepository,
        vectors: KnowledgeVectorStore,
        embeddings: EmbeddingProvider,
        clock: Clock,
        training_index: TrainingSessionIndexRepository | None = None,
    ) -> None:
        self._agents = agents
        self._instructions = instructions
        self._vectors = vectors
        self._embeddings = embeddings
        self._clock = clock
        self._training_index = training_index

    def execute(
        self,
        *,
        agent_id: uuid.UUID,
        actor_tenant_id: uuid.UUID | None,
        privileged: bool,
        kind: str = "test",
        query: str = "",
    ) -> dict:
        agent = _load_agent(self._agents, agent_id, actor_tenant_id, privileged)
        assert_test_routable(status=agent.status)
        try:
            session_kind = TestSessionKind(kind)
        except ValueError as exc:
            raise DomainError("validation_error", "kind is invalid.") from exc
        now = self._clock.now()
        if agent.status is AgentStatus.DRAFT:
            agent = self._agents.put_agent(
                agent.tenant_id,
                replace(agent, status=AgentStatus.TESTING, updated_at=now),
            )
        session = self._agents.put_session(
            agent.tenant_id,
            TestSessionRecord(
                session_id=new_uuid7(),
                tenant_id=agent.tenant_id,
                customer_id=agent.customer_id,
                agent_id=agent.agent_id,
                kind=session_kind.value,
                status=TestSessionStatus.OPEN.value,
                created_at=now,
            ),
        )
        if self._training_index is not None:
            self._training_index.save(
                session_id=session.session_id,
                tenant_id=agent.tenant_id,
                customer_id=agent.customer_id,
                agent_id=agent.agent_id,
            )
        attachments = self._agents.list_attachments(agent.tenant_id, agent.agent_id)
        group_ids = [row.group_id for row in attachments]
        hits = []
        if query.strip() and group_ids:
            hits = self._vectors.search(group_ids, self._embeddings.embed(query), top_k=5)
        log_event(
            logger,
            "agent.test_session.started",
            outcome="success",
            tenant_id=str(agent.tenant_id),
            agent_id=str(agent.agent_id),
            session_id=str(session.session_id),
        )
        return {
            "id": str(session.session_id),
            "agent_id": str(agent.agent_id),
            "kind": session.kind,
            "status": session.status,
            "agent_status": agent.status.value,
            "production_routable": False,
            "resolved_instructions": resolve_for_agent(agent, self._agents, self._instructions),
            "knowledge_group_ids": group_ids,
            "knowledge_hits": hits,
        }


class SaveInstruction:
    def __init__(self, agents: TenantAgentService, clock: Clock) -> None:
        self._agents = agents
        self._clock = clock

    def execute(
        self,
        *,
        tenant_id: uuid.UUID,
        scope: str,
        owner_id: uuid.UUID,
        body: str,
        actor_tenant_id: uuid.UUID | None,
        privileged: bool,
    ) -> dict:
        if scope not in {"agency", "customer"}:
            raise DomainError("validation_error", "scope is invalid.")
        if not privileged:
            if actor_tenant_id is None or actor_tenant_id != tenant_id:
                raise DomainError("not_found", "Resource not found.", http_status=404)
        from control_plane.agents.domain.policies import assert_no_secrets
        from tenant.agents.domain import InstructionLayerRecord

        assert_no_secrets(body, field="instructions")
        self._agents.put_instruction(
            tenant_id,
            InstructionLayerRecord(
                tenant_id=tenant_id,
                scope=scope,
                owner_id=owner_id,
                body=body,
                updated_at=self._clock.now(),
            ),
        )
        return {"scope": scope, "owner_id": str(owner_id), "body": body}
