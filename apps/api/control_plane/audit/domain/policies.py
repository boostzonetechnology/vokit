from __future__ import annotations

from typing import Any

from control_plane.audit.domain.types import (
    HIGH_RISK_ACTIONS,
    OVERRIDE_ACTIONS,
    AuditSeverity,
)
from shared_kernel.errors import DomainError
from shared_kernel.logging import FORBIDDEN_KEYS


def assert_override_reason(action: str, reason: str) -> str:
    cleaned = reason.strip()
    if action in OVERRIDE_ACTIONS and not cleaned:
        raise DomainError("validation_error", "reason is required.")
    return cleaned[:255]


def severity_for(action: str) -> AuditSeverity:
    if action in HIGH_RISK_ACTIONS:
        return AuditSeverity.HIGH
    return AuditSeverity.INFO


def redact_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        lowered = str(key).lower()
        if lowered in FORBIDDEN_KEYS or any(part in lowered for part in FORBIDDEN_KEYS):
            redacted[str(key)] = "[redacted]"
            continue
        if isinstance(value, dict):
            redacted[str(key)] = redact_payload(value)
            continue
        redacted[str(key)] = value
    return redacted


def assert_immutable() -> None:
    raise DomainError(
        "audit_immutable",
        "Audit events cannot be edited or deleted.",
        http_status=409,
    )
