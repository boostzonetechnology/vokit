from __future__ import annotations

from django.conf import settings

from control_plane.agents.application.builder import (
    CloneAgent,
    ConfigureAgent,
    PauseAgent,
    PublishAgent,
    ResumeAgent,
    SetAgentStatus,
)
from control_plane.agents.application.knowledge import (
    AttachKnowledge,
    DeleteKnowledge,
    DetachKnowledge,
    IngestKnowledge,
    ProcessKnowledge,
)
from control_plane.agents.application.sessions import SaveInstruction, StartTestSession
from control_plane.agents.application.templates import CreateTemplate, InstallTemplate
from control_plane.agents.infrastructure.extract import extract_knowledge_text
from control_plane.agents.infrastructure.repositories import (
    DjangoAgentIndexRepository,
    DjangoGlobalInstructionRepository,
    DjangoGlobalKnowledgeRepository,
    DjangoTemplateRepository,
    DjangoTemplateVersionRepository,
)
from control_plane.agents.infrastructure.vectors import (
    HashEmbedding,
    MemoryVectorStore,
    QdrantHttpStore,
)
from control_plane.customers.infrastructure.container import customer_index
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.risk.infrastructure.container import risk_gate, tenant_agents
from control_plane.tenancy.infrastructure.container import lifecycle, router, runtime
from tenant.billing.service import TenantBillingService

_memory_vectors: MemoryVectorStore | None = None


def reset_vectors() -> None:
    global _memory_vectors
    _memory_vectors = None


def templates() -> DjangoTemplateRepository:
    return DjangoTemplateRepository()


def template_versions() -> DjangoTemplateVersionRepository:
    return DjangoTemplateVersionRepository()


def agent_index() -> DjangoAgentIndexRepository:
    return DjangoAgentIndexRepository()


def global_instructions() -> DjangoGlobalInstructionRepository:
    return DjangoGlobalInstructionRepository()


def global_knowledge() -> DjangoGlobalKnowledgeRepository:
    return DjangoGlobalKnowledgeRepository()


def embeddings() -> HashEmbedding:
    return HashEmbedding()


def vector_store() -> MemoryVectorStore | QdrantHttpStore:
    url = str(getattr(settings, "QDRANT_URL", "") or "").strip()
    collection = str(getattr(settings, "QDRANT_COLLECTION", "vokit_knowledge"))
    if url:
        return QdrantHttpStore(url, collection)
    global _memory_vectors
    if _memory_vectors is None:
        _memory_vectors = MemoryVectorStore()
    return _memory_vectors


def tenant_billing() -> TenantBillingService:
    return TenantBillingService(router(), runtime())


def configure_agent() -> ConfigureAgent:
    return ConfigureAgent(customer_index(), tenant_agents(), agent_index(), SystemClock())


def publish_agent() -> PublishAgent:
    return PublishAgent(
        customer_index(),
        lifecycle(),
        tenant_billing(),
        tenant_agents(),
        global_instructions(),
        risk_gate(),
        agent_index(),
        SystemClock(),
    )


def pause_agent() -> PauseAgent:
    return PauseAgent(tenant_agents(), agent_index(), SystemClock())


def resume_agent() -> ResumeAgent:
    return ResumeAgent(tenant_agents(), agent_index(), SystemClock())


def set_agent_status() -> SetAgentStatus:
    return SetAgentStatus(tenant_agents(), agent_index(), SystemClock())


def clone_agent() -> CloneAgent:
    return CloneAgent(
        customer_index(), tenant_agents(), risk_gate(), agent_index(), SystemClock()
    )


def create_template() -> CreateTemplate:
    return CreateTemplate(templates(), template_versions(), SystemClock())


def install_template() -> InstallTemplate:
    return InstallTemplate(
        templates(),
        template_versions(),
        customer_index(),
        lifecycle(),
        tenant_agents(),
        risk_gate(),
        agent_index(),
        SystemClock(),
    )


class CeleryKnowledgeJobQueue:
    def enqueue_process(
        self, *, source_id, tenant_id, correlation_id: str
    ) -> None:
        from control_plane.agents.tasks import process_knowledge_source_task

        process_knowledge_source_task.delay(
            str(source_id),
            str(tenant_id) if tenant_id else None,
            correlation_id,
        )


def ingest_knowledge() -> IngestKnowledge:
    return IngestKnowledge(
        tenant_agents(),
        global_knowledge(),
        SystemClock(),
        customer_index(),
        CeleryKnowledgeJobQueue(),
        extract_knowledge_text,
    )


def process_knowledge() -> ProcessKnowledge:
    return ProcessKnowledge(
        tenant_agents(),
        vector_store(),
        embeddings(),
        global_knowledge(),
        SystemClock(),
    )


def attach_knowledge() -> AttachKnowledge:
    return AttachKnowledge(tenant_agents(), global_knowledge())


def detach_knowledge() -> DetachKnowledge:
    return DetachKnowledge(tenant_agents())


def delete_knowledge() -> DeleteKnowledge:
    return DeleteKnowledge(tenant_agents(), vector_store(), global_knowledge())


def start_test_session() -> StartTestSession:
    from control_plane.telephony.infrastructure.repositories import (
        DjangoTrainingSessionIndex,
    )

    return StartTestSession(
        tenant_agents(),
        global_instructions(),
        vector_store(),
        embeddings(),
        SystemClock(),
        DjangoTrainingSessionIndex(),
    )


def save_instruction() -> SaveInstruction:
    return SaveInstruction(tenant_agents(), SystemClock())
