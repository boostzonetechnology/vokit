from __future__ import annotations

from pathlib import Path

import pytest
from django.core.management import CommandError, call_command
from django.test import Client, override_settings
from django.test.utils import captured_stdout

from config.settings.hardening import assert_production_boot
from control_plane.ops.application.gate import ProductionReadiness
from control_plane.ops.application.live_flags import assert_billing_live, assert_calling_live
from control_plane.ops.domain.policies import parse_attestation
from control_plane.ops.domain.types import GateMode, GateVerdict
from control_plane.ops.infrastructure.container import post_deploy_smoke, repo_root
from control_plane.platform_settings.application.ports import SettingRecord
from control_plane.platform_settings.infrastructure.repositories import DjangoSettingRepository
from control_plane.recordings.application.service import IngestCommand
from control_plane.recordings.infrastructure.container import recording_control
from control_plane.telephony.infrastructure.container import voice_control
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7

_DATED = {
    "VOKIT_EVIDENCE_LIVE_INBOUND_CALL": "2026-09-10",
    "VOKIT_EVIDENCE_LIVE_OUTBOUND_CALL": "2026-09-10",
    "VOKIT_EVIDENCE_LIVE_PAYMENT": "2026-09-10",
    "VOKIT_EVIDENCE_LIVE_RECORDING": "2026-09-10",
    "VOKIT_EVIDENCE_RESTORE_DRILL": "2026-09-10",
    "VOKIT_EVIDENCE_ALERTING": "2026-09-10",
    "VOKIT_EVIDENCE_ROLLBACK_STAGING": "2026-09-10",
    "VOKIT_EVIDENCE_LEGAL_SIGN_OFF": "2026-09-10",
}


def test_attestation_rejects_boolean_flags() -> None:
    assert parse_attestation("true") is None
    assert parse_attestation("1") is None
    assert parse_attestation("2026-09-10") == "2026-09-10"


def test_lab_gate_is_ready_without_live_attestations() -> None:
    report = ProductionReadiness(repo_root(), {}).execute(GateMode.LAB)
    assert report.verdict is GateVerdict.LAB_READY
    assert all(row.item.kind.value != "attestation" for row in report.checks)


def test_production_gate_is_no_go_without_dated_evidence() -> None:
    report = ProductionReadiness(repo_root(), {"VOKIT_LAUNCH_GO": "1"}).execute(
        GateMode.PRODUCTION
    )
    assert report.verdict is GateVerdict.NO_GO
    live = [row for row in report.checks if row.item.section == "live"]
    assert live
    assert all(not row.passed for row in live)


def test_production_gate_goes_only_with_dated_attestations() -> None:
    report = ProductionReadiness(repo_root(), _DATED).execute(GateMode.PRODUCTION)
    assert report.verdict is GateVerdict.GO


def test_production_boot_fails_closed() -> None:
    with pytest.raises(DomainError) as exc:
        assert_production_boot(
            allowed_hosts=["api.vokit.example"],
            telephony_token="",
            recording_token="rec-token",
            cors_origins=["https://app.example"],
            csrf_origins=["https://app.example"],
            tenant_runtime="mysql",
            tenant_tls_required=True,
        )
    assert exc.value.code == "invalid_configuration"
    with pytest.raises(DomainError):
        assert_production_boot(
            allowed_hosts=["api.vokit.example"],
            telephony_token="same",
            recording_token="same",
            cors_origins=["https://app.example"],
            csrf_origins=["https://app.example"],
            tenant_runtime="mysql",
            tenant_tls_required=True,
        )
    assert_production_boot(
        allowed_hosts=["api.vokit.example"],
        telephony_token="tel-token",
        recording_token="rec-token",
        cors_origins=["https://app.example"],
        csrf_origins=["https://app.example"],
        tenant_runtime="mysql",
        tenant_tls_required=True,
    )


@pytest.mark.django_db
@override_settings(VOKIT_PRODUCTION_HARDENING=True, VOKIT_INTERNAL_TELEPHONY_TOKEN="")
def test_production_readiness_fails_without_telephony_token() -> None:
    response = Client().get("/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "not_ready"


@pytest.mark.django_db
@override_settings(LIVE_FLAGS_ENABLED_BY_DEFAULT=False)
def test_live_flags_block_calling_billing_and_recordings() -> None:
    resolved = voice_control().resolve_did("+15551234567")
    assert resolved == {"routable": False, "reason": "calling_not_live"}
    boot = voice_control().bootstrap(
        did="+15551234567",
        edge_call_id="edge-1",
        from_number="+15550000000",
        sip_call_id="sip-1",
        direction="inbound",
    )
    assert boot["admitted"] is False
    assert boot["reject_reason"] == "calling_not_live"
    with pytest.raises(DomainError) as calling:
        voice_control().originate(
            tenant_id=new_uuid7(),
            agent_id=new_uuid7(),
            to="+15551234567",
            actor_id=new_uuid7(),
            idempotency_key="k1",
        )
    assert calling.value.code == "feature_flag_disabled"
    with pytest.raises(DomainError) as billing:
        assert_billing_live()
    assert billing.value.code == "feature_flag_disabled"
    with pytest.raises(DomainError) as recording:
        recording_control().ingest(
            IngestCommand(
                event_id="evt-new",
                edge_call_id="edge-1",
                call_id="",
                artifact_id="",
                kind="mix",
                content_type="audio/wav",
                size_bytes=8,
                checksum="sha256:" + ("ab" * 32),
            )
        )
    assert recording.value.code == "feature_flag_disabled"


@pytest.mark.django_db
def test_stored_flag_overrides_lab_default() -> None:
    DjangoSettingRepository().upsert(
        SettingRecord(
            key="flags.calling_live",
            value=False,
            secret=False,
            updated_by_id=None,
        )
    )
    with pytest.raises(DomainError) as exc:
        assert_calling_live()
    assert exc.value.code == "feature_flag_disabled"


@pytest.mark.django_db
def test_post_deploy_smoke_and_lab_command(tmp_path: Path) -> None:
    payload = post_deploy_smoke().execute()
    assert payload["status"] == "ok"
    assert payload["checks"]["health"] == 200
    out = tmp_path / "lab-gate.json"
    with captured_stdout() as stdout:
        call_command("check_production_readiness", "--lab", f"--out={out}")
    assert "LAB_READY" in stdout.getvalue()
    assert out.is_file()
    with pytest.raises(CommandError):
        call_command("check_production_readiness")
