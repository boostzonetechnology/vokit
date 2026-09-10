from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timedelta

from control_plane.recordings.domain.types import ArtifactKind, ArtifactStatus
from shared_kernel.errors import DomainError

_CHECKSUM = re.compile(r"^sha256:[0-9a-f]{64}$")
_CONTENT = re.compile(r"^[a-z0-9]+/[a-z0-9.+-]+$")


def object_key(*, tenant_id: uuid.UUID, call_id: uuid.UUID, artifact_id: uuid.UUID) -> str:
    return f"tenant/{tenant_id}/calls/{call_id}/artifacts/{artifact_id}"


def assert_checksum(raw: str) -> str:
    value = (raw or "").strip().lower()
    if not _CHECKSUM.match(value):
        raise DomainError("validation_error", "checksum must be sha256:<hex>.")
    return value


def assert_content_type(raw: str) -> str:
    value = (raw or "").strip().lower()
    if not _CONTENT.match(value):
        raise DomainError("validation_error", "content_type is invalid.")
    return value[:128]


def assert_kind(raw: str) -> ArtifactKind:
    try:
        return ArtifactKind((raw or "").strip().lower())
    except ValueError as exc:
        raise DomainError("validation_error", "artifact kind is invalid.") from exc


def assert_size(raw: object) -> int:
    if type(raw) is not int or raw < 1:
        raise DomainError("validation_error", "size_bytes must be a positive integer.")
    return raw


def retention_until(now: datetime, *, days: int) -> datetime:
    if type(days) is not int or days < 1:
        raise DomainError("validation_error", "retention_days must be >= 1.")
    return now + timedelta(days=days)


def assert_ready_for_access(status: ArtifactStatus) -> None:
    if status not in {ArtifactStatus.READY, ArtifactStatus.RETAINED}:
        raise DomainError("not_found", "Resource not found.", http_status=404)


def assert_can_delete(
    *,
    status: ArtifactStatus,
    legal_hold: bool,
    now: datetime,
    until: datetime,
) -> None:
    if status is ArtifactStatus.DELETED:
        return
    if legal_hold:
        raise DomainError(
            "conflict_state",
            "Artifact is on legal hold.",
            http_status=409,
            details={"reason": "legal_hold"},
        )
    if now < until:
        raise DomainError(
            "conflict_state",
            "Retention period has not elapsed.",
            http_status=409,
            details={"reason": "retention"},
        )


def next_status_after_hold(*, legal_hold: bool, status: ArtifactStatus) -> ArtifactStatus:
    if status is ArtifactStatus.DELETED:
        raise DomainError("conflict_state", "Deleted artifacts cannot change hold.")
    if legal_hold:
        return ArtifactStatus.RETAINED
    if status is ArtifactStatus.RETAINED:
        return ArtifactStatus.READY
    return status


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def assert_same_scope(
    *,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    call_id: uuid.UUID,
    expected_tenant: uuid.UUID,
    expected_customer: uuid.UUID,
    expected_call: uuid.UUID,
) -> None:
    if (
        tenant_id != expected_tenant
        or customer_id != expected_customer
        or call_id != expected_call
    ):
        raise DomainError("not_found", "Resource not found.", http_status=404)
