"""Regression locks for lab inbound wiring (Asterisk VM → Windows Django/Edge/Pipecat)."""

from __future__ import annotations

import json
from pathlib import Path

from django.test import Client

from control_plane.telephony.api.internal import _require_internal


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_dev_voice_starts_pipecat_app_module() -> None:
    script = (_repo_root() / "scripts" / "dev-voice.ps1").read_text(encoding="utf-8")
    assert "vokit_pipecat_voice.app:app" in script
    assert "app.main:app" not in script


def test_local_settings_allow_vmware_host_ip() -> None:
    text = (
        _repo_root() / "apps" / "api" / "config" / "settings" / "local.py"
    ).read_text(encoding="utf-8")
    assert "192.168.56.1" in text


def test_internal_telephony_token_header_is_x_vokit_internal_token() -> None:
    source = Path(_require_internal.__code__.co_filename).read_text(encoding="utf-8")
    assert "X-Vokit-Internal-Token" in source
    assert "Authorization" not in source.split("def _require_internal", 1)[1].split("class ", 1)[0]


def test_asterisk_lab_dialplan_uses_internal_token_header() -> None:
    dialplan = (
        _repo_root() / "deploy" / "asterisk" / "lab" / "extensions.conf"
    ).read_text(encoding="utf-8")
    assert "X-Vokit-Internal-Token" in dialplan
    assert "CURLOPT(httpheader)=Authorization" not in dialplan


def test_did_resolve_rejects_authorization_bearer_header() -> None:
    client = Client()
    response = client.post(
        "/internal/telephony/v1/did-resolve/",
        data=json.dumps({"did": "15550001001"}),
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer test-internal-telephony-token",
    )
    assert response.status_code == 401
