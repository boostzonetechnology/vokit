from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from control_plane.recordings.domain.policies import (
    assert_can_delete,
    assert_checksum,
    assert_kind,
    assert_ready_for_access,
    assert_same_scope,
    hash_token,
    next_status_after_hold,
    object_key,
    retention_until,
)
from control_plane.recordings.domain.types import ArtifactKind, ArtifactStatus
from shared_kernel.errors import DomainError


def test_object_key_is_tenant_partitioned() -> None:
    tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    call_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    artifact_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    assert object_key(
        tenant_id=tenant_id, call_id=call_id, artifact_id=artifact_id
    ) == (
        "tenant/11111111-1111-1111-1111-111111111111/"
        "calls/22222222-2222-2222-2222-222222222222/"
        "artifacts/33333333-3333-3333-3333-333333333333"
    )


def test_checksum_and_kind_validation() -> None:
    digest = "ab" * 32
    assert assert_checksum(f"SHA256:{digest}") == f"sha256:{digest}"
    assert assert_kind("call_recording") is ArtifactKind.CALL_RECORDING
    with pytest.raises(DomainError) as checksum_exc:
        assert_checksum("md5:abc")
    assert checksum_exc.value.code == "validation_error"
    with pytest.raises(DomainError):
        assert_kind("waveform")


def test_access_and_delete_states() -> None:
    now = datetime(2026, 9, 10, tzinfo=UTC)
    until = retention_until(now, days=30)
    assert until == now + timedelta(days=30)
    assert_ready_for_access(ArtifactStatus.READY)
    with pytest.raises(DomainError) as access_exc:
        assert_ready_for_access(ArtifactStatus.VERIFYING)
    assert access_exc.value.http_status == 404
    with pytest.raises(DomainError) as hold_exc:
        assert_can_delete(
            status=ArtifactStatus.READY,
            legal_hold=True,
            now=now,
            until=until,
        )
    assert hold_exc.value.details["reason"] == "legal_hold"
    with pytest.raises(DomainError) as retain_exc:
        assert_can_delete(
            status=ArtifactStatus.READY,
            legal_hold=False,
            now=now,
            until=until,
        )
    assert retain_exc.value.details["reason"] == "retention"
    assert_can_delete(
        status=ArtifactStatus.READY,
        legal_hold=False,
        now=until,
        until=until,
    )
    assert next_status_after_hold(
        legal_hold=True, status=ArtifactStatus.READY
    ) is ArtifactStatus.RETAINED
    assert next_status_after_hold(
        legal_hold=False, status=ArtifactStatus.RETAINED
    ) is ArtifactStatus.READY


def test_token_hash_and_scope_mismatch() -> None:
    assert hash_token("one") != hash_token("two")
    tenant = uuid.uuid4()
    customer = uuid.uuid4()
    call = uuid.uuid4()
    assert_same_scope(
        tenant_id=tenant,
        customer_id=customer,
        call_id=call,
        expected_tenant=tenant,
        expected_customer=customer,
        expected_call=call,
    )
    with pytest.raises(DomainError) as exc:
        assert_same_scope(
            tenant_id=tenant,
            customer_id=customer,
            call_id=call,
            expected_tenant=tenant,
            expected_customer=customer,
            expected_call=uuid.uuid4(),
        )
    assert exc.value.http_status == 404
