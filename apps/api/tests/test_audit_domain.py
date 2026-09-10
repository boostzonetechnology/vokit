from __future__ import annotations

import pytest

from control_plane.audit.domain.policies import (
    assert_immutable,
    assert_override_reason,
    redact_payload,
    severity_for,
)
from control_plane.audit.domain.types import AuditSeverity
from shared_kernel.errors import DomainError


def test_override_reason_is_required() -> None:
    with pytest.raises(DomainError) as exc:
        assert_override_reason("kyc.override", "  ")
    assert exc.value.code == "validation_error"
    assert assert_override_reason("kyc.override", "freeze payouts") == "freeze payouts"


def test_high_risk_severity_and_redaction() -> None:
    assert severity_for("kyc.override") is AuditSeverity.HIGH
    assert severity_for("login") is AuditSeverity.INFO
    payload = redact_payload(
        {"action": "freeze", "api_key": "secret-value", "note": "ok"}
    )
    assert payload["api_key"] == "[redacted]"
    assert payload["note"] == "ok"


def test_audit_rows_cannot_be_mutated() -> None:
    with pytest.raises(DomainError) as exc:
        assert_immutable()
    assert exc.value.code == "audit_immutable"
