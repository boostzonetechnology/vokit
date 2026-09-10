from __future__ import annotations

from dataclasses import dataclass

from control_plane.agents.domain.types import (
    AGENT_TYPES,
    ALLOWED_TOOLS,
    FALLBACKS,
    PRODUCTION_STATUSES,
    TEST_STATUSES,
    KnowledgeScope,
)
from control_plane.customers.domain.types import CustomerStatus
from control_plane.risk.domain.types import AgentStatus
from shared_kernel.errors import DomainError

SECRET_MARKERS = (
    "api_key=",
    "apikey=",
    "authorization:",
    "bearer ",
    "password=",
    "-----begin",
    "sk_live",
    "sk_test",
)


@dataclass(frozen=True, slots=True)
class InstructionLayers:
    platform_safety: str = ""
    template_base: str = ""
    agency: str = ""
    customer: str = ""
    agent: str = ""


def assert_agent_type(value: str) -> str:
    normalized = (value or "custom").strip().lower() or "custom"
    if normalized not in AGENT_TYPES:
        raise DomainError("validation_error", "agent_type is invalid.")
    return normalized


def assert_tools(tools: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in tools:
        name = str(raw).strip()
        if not name or name in seen:
            continue
        if name not in ALLOWED_TOOLS:
            raise DomainError("invalid_tool", f"Tool '{name}' is not allowlisted.", http_status=422)
        seen.add(name)
        cleaned.append(name)
    return tuple(cleaned)


def assert_fallback(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized not in FALLBACKS:
        raise DomainError("validation_error", "fallback_behavior is invalid.")
    return normalized


def assert_no_secrets(text: str, *, field: str = "text") -> None:
    blob = (text or "").lower()
    if any(marker in blob for marker in SECRET_MARKERS):
        raise DomainError(
            "secret_in_prompt",
            f"{field} must not contain credentials or private keys.",
            http_status=422,
        )


def resolve_instructions(layers: InstructionLayers) -> str:
    parts: list[str] = []
    if layers.platform_safety.strip():
        parts.append(f"[PLATFORM SAFETY]\n{layers.platform_safety.strip()}")
    if layers.template_base.strip():
        parts.append(f"[TEMPLATE]\n{layers.template_base.strip()}")
    if layers.agency.strip():
        parts.append(f"[AGENCY]\n{layers.agency.strip()}")
    if layers.customer.strip():
        parts.append(f"[CUSTOMER]\n{layers.customer.strip()}")
    if layers.agent.strip():
        parts.append(f"[AGENT]\n{layers.agent.strip()}")
    return "\n\n".join(parts)


def knowledge_group_id(
    scope: KnowledgeScope,
    *,
    tenant_id: str = "",
    customer_id: str = "",
    agent_id: str = "",
) -> str:
    if scope is KnowledgeScope.GLOBAL:
        return "global"
    if scope is KnowledgeScope.AGENCY:
        return f"agency:{tenant_id}"
    if scope is KnowledgeScope.CUSTOMER:
        return f"customer:{customer_id}"
    return f"agent:{agent_id}"


def chunk_text(text: str, *, size: int = 800) -> list[str]:
    body = (text or "").strip()
    if not body:
        return []
    return [body[index : index + size] for index in range(0, len(body), size)]


def agent_not_routable(reason: str = "unpublished") -> DomainError:
    return DomainError(
        "agent_not_routable",
        "Agent is not available for production routing.",
        http_status=409,
        details={"reason": reason},
    )


def assert_production_routable(*, status: AgentStatus, published_version: int | None) -> None:
    if status is AgentStatus.SUSPENDED:
        raise agent_not_routable("suspended")
    if status is AgentStatus.PAUSED:
        raise agent_not_routable("paused")
    if status is AgentStatus.ARCHIVED:
        raise agent_not_routable("archived")
    if status not in PRODUCTION_STATUSES or published_version is None:
        raise agent_not_routable("unpublished")


def assert_test_routable(*, status: AgentStatus) -> None:
    if status not in TEST_STATUSES:
        raise agent_not_routable(status.value)


def publish_failures(
    *,
    customer_status: CustomerStatus | None,
    has_subscription: bool,
    resolved_instructions: str,
    voice_provider: str,
    voice_id: str,
    language: str,
    recording_disclosure: bool | None,
    fallback_behavior: str,
    status: AgentStatus,
) -> list[str]:
    failures: list[str] = []
    if customer_status is not CustomerStatus.ACTIVE:
        failures.append("customer_inactive")
    if not has_subscription:
        failures.append("subscription_required")
    if not resolved_instructions.strip():
        failures.append("instructions_required")
    if not voice_provider.strip() or not voice_id.strip() or not language.strip():
        failures.append("voice_required")
    if recording_disclosure is None:
        failures.append("compliance_required")
    if fallback_behavior not in FALLBACKS:
        failures.append("fallback_required")
    if status is AgentStatus.SUSPENDED:
        failures.append("agent_suspended")
    if status is AgentStatus.ARCHIVED:
        failures.append("agent_archived")
    return failures
