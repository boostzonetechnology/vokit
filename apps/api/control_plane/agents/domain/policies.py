from __future__ import annotations

import hashlib
from dataclasses import dataclass

from control_plane.agents.domain.types import (
    AGENT_TYPES,
    ALLOWED_TOOLS,
    DEFAULT_MAX_CALL_DURATION_SECONDS,
    DEFAULT_SILENCE_TIMEOUT_SECONDS,
    FALLBACKS,
    MAX_CALL_DURATION_RANGE,
    PERSONA_FIELD_MAX,
    PRODUCTION_STATUSES,
    RESTRICTIVE_STATUSES,
    ROLE_FIELD_MAX,
    SILENCE_TIMEOUT_RANGE,
    SPEAKING_SPEED_RANGE,
    SPEAKING_STYLE_MAX,
    TEST_STATUSES,
    KnowledgeScope,
    KnowledgeStatus,
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
    role: str = ""
    goals: str = ""
    constraints: str = ""
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
    persona: list[str] = []
    if layers.role.strip():
        persona.append(f"Role: {layers.role.strip()}")
    if layers.goals.strip():
        persona.append(f"Goals: {layers.goals.strip()}")
    if layers.constraints.strip():
        persona.append(f"Constraints: {layers.constraints.strip()}")
    if persona:
        parts.append("[PERSONA]\n" + "\n".join(persona))
    if layers.agent.strip():
        parts.append(f"[AGENT]\n{layers.agent.strip()}")
    return "\n\n".join(parts)


def assert_speaking_style(value: str) -> str:
    cleaned = (value or "").strip()
    if len(cleaned) > SPEAKING_STYLE_MAX:
        raise DomainError("validation_error", "speaking_style is too long.")
    assert_no_secrets(cleaned, field="speaking_style")
    return cleaned


def assert_speaking_speed(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        speed = float(value)
    except (TypeError, ValueError) as exc:
        raise DomainError("validation_error", "speaking_speed is invalid.") from exc
    low, high = SPEAKING_SPEED_RANGE
    if speed < low or speed > high:
        raise DomainError("validation_error", "speaking_speed is out of range.")
    return speed


def assert_persona_field(value: str, *, field: str, limit: int = PERSONA_FIELD_MAX) -> str:
    cleaned = value or ""
    if field == "role":
        cleaned = cleaned.strip()
        limit = ROLE_FIELD_MAX
    if len(cleaned) > limit:
        raise DomainError("validation_error", f"{field} is too long.")
    assert_no_secrets(cleaned, field=field)
    return cleaned


def assert_silence_timeout(value: object) -> int:
    return _bounded_int(
        value,
        field="silence_timeout_seconds",
        default=DEFAULT_SILENCE_TIMEOUT_SECONDS,
        bounds=SILENCE_TIMEOUT_RANGE,
    )


def assert_max_call_duration(value: object) -> int:
    return _bounded_int(
        value,
        field="max_call_duration_seconds",
        default=DEFAULT_MAX_CALL_DURATION_SECONDS,
        bounds=MAX_CALL_DURATION_RANGE,
    )


def _bounded_int(
    value: object, *, field: str, default: int, bounds: tuple[int, int]
) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise DomainError("validation_error", f"{field} is invalid.") from exc
    low, high = bounds
    if parsed < low or parsed > high:
        raise DomainError("validation_error", f"{field} is out of range.")
    return parsed


def knowledge_checksum(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def assert_knowledge_attach_scope(*, agent, source) -> None:
    scope = str(getattr(source, "scope", "") or "")
    owner_id = getattr(source, "owner_id", None)
    if scope == KnowledgeScope.CUSTOMER.value and owner_id != agent.customer_id:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    if scope == KnowledgeScope.AGENT.value and owner_id != agent.agent_id:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    status = str(getattr(source, "status", "") or "")
    if status != KnowledgeStatus.READY.value:
        raise DomainError(
            "knowledge_not_ready",
            "Knowledge source is not ready to attach.",
            http_status=409,
        )


def knowledge_in_use(agent_ids: list[str]) -> DomainError:
    return DomainError(
        "knowledge_in_use",
        "Deleting this source detaches it from attached agents. Retry with confirm=true.",
        http_status=409,
        details={
            "attached_agent_ids": agent_ids,
            "attached_count": len(agent_ids),
        },
    )


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
    if not voice_id.strip() or not language.strip():
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


def assert_status_unlocked(agent) -> None:
    if getattr(agent, "status_locked", False):
        raise DomainError(
            "agent_status_locked",
            "Only Super Admin can change this agent status.",
            http_status=409,
        )


def parse_agent_status(value: object) -> AgentStatus:
    raw = str(value or "").strip().lower()
    try:
        return AgentStatus(raw)
    except ValueError as exc:
        raise DomainError("validation_error", "status is invalid.") from exc


def platform_lock_flags(status: AgentStatus) -> tuple[bool, str]:
    if status in RESTRICTIVE_STATUSES:
        return True, "platform"
    return False, "platform"
