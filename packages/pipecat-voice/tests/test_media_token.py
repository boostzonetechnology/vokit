"""Media token gate, health, and outbound echo (no AI)."""
from __future__ import annotations

import json
from dataclasses import replace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import vokit_pipecat_voice.app as app_mod


def _set_media_token(monkeypatch, token: str) -> None:
    monkeypatch.setattr(app_mod, "config", replace(app_mod.config, media_ws_token=token))


def test_health():
    client = TestClient(app_mod.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["codec"] == "pcmu"
    assert body["sample_rate"] == 8000


def test_media_ws_rejects_wrong_token(monkeypatch):
    _set_media_token(monkeypatch, "expected-token")
    client = TestClient(app_mod.app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/sip/media?media_token=wrong"):
            pass


def test_outbound_echo_does_not_call_django(monkeypatch):
    _set_media_token(monkeypatch, "tok")
    bootstrap = AsyncMock()
    monkeypatch.setattr(app_mod.django, "bootstrap", bootstrap)
    client = TestClient(app_mod.app)
    with client.websocket_connect("/sip/media?media_token=tok") as ws:
        ws.send_text(
            json.dumps(
                {
                    "type": "start",
                    "call_id": "out-1",
                    "from": "+1",
                    "to": "+2",
                    "direction": "outbound",
                }
            )
        )
        ws.send_bytes(b"\xff" * 160)
        echoed = ws.receive_bytes()
        assert echoed == b"\xff" * 160
        ws.send_text(json.dumps({"type": "stop", "reason": "call_ended"}))
    bootstrap.assert_not_called()


def test_inbound_django_unreachable_fails_closed(monkeypatch):
    from vokit_pipecat_voice.django_client import DjangoUnreachable

    _set_media_token(monkeypatch, "tok")
    monkeypatch.setattr(
        app_mod.django,
        "bootstrap",
        AsyncMock(side_effect=DjangoUnreachable("down")),
    )
    client = TestClient(app_mod.app)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/sip/media?media_token=tok") as ws:
            ws.send_text(
                json.dumps(
                    {
                        "type": "start",
                        "call_id": "in-1",
                        "from": "+1",
                        "to": "+2",
                        "direction": "inbound",
                    }
                )
            )
            ws.receive_text()
    assert exc.value.code == 4403


def test_inbound_not_admitted_fails_closed(monkeypatch):
    _set_media_token(monkeypatch, "tok")
    monkeypatch.setattr(
        app_mod.django,
        "bootstrap",
        AsyncMock(return_value={"admitted": False, "reject_reason": "insufficient_balance"}),
    )
    run_pipeline = AsyncMock()
    monkeypatch.setattr(app_mod, "run_inbound_pipeline", run_pipeline)
    client = TestClient(app_mod.app)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/sip/media?media_token=tok") as ws:
            ws.send_text(
                json.dumps(
                    {
                        "type": "start",
                        "call_id": "in-2",
                        "from": "+1",
                        "to": "+2",
                        "direction": "inbound",
                    }
                )
            )
            ws.receive_text()
    assert exc.value.code == 4403
    run_pipeline.assert_not_called()


def test_inbound_admitted_starts_pipeline(monkeypatch):
    _set_media_token(monkeypatch, "tok")
    bootstrap = AsyncMock(
        return_value={
            "admitted": True,
            "edge_call_id": "in-3",
            "agent": {"welcome_greeting": "Hi"},
            "providers": {},
            "timers": {},
        }
    )
    run_pipeline = AsyncMock()
    monkeypatch.setattr(app_mod.django, "bootstrap", bootstrap)
    monkeypatch.setattr(app_mod, "run_inbound_pipeline", run_pipeline)
    client = TestClient(app_mod.app)
    with client.websocket_connect("/sip/media?media_token=tok") as ws:
        ws.send_text(
            json.dumps(
                {
                    "type": "start",
                    "call_id": "in-3",
                    "from": "+1",
                    "to": "+2",
                    "direction": "inbound",
                }
            )
        )
        ws.close()
    bootstrap.assert_awaited_once()
    run_pipeline.assert_awaited_once()


def test_training_offer_requires_session_token():
    client = TestClient(app_mod.app)
    resp = client.post("/training/webrtc/offer", json={"sdp": "x", "type": "offer"})
    assert resp.status_code == 400
