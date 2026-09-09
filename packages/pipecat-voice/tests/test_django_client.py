"""Django client fail-closed behavior."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from vokit_pipecat_voice.config import PipecatVoiceConfig
from vokit_pipecat_voice.django_client import DjangoUnreachable, DjangoVoiceClient


def _config() -> PipecatVoiceConfig:
    return PipecatVoiceConfig(
        media_ws_token="tok",
        django_internal_base_url="http://django.test",
        internal_telephony_token="internal",
        host="0.0.0.0",
        port=8100,
        heartbeat_seconds=2,
    )


@pytest.mark.asyncio
async def test_bootstrap_network_error_is_unreachable():
    client = DjangoVoiceClient(_config())
    with patch("httpx.AsyncClient") as cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = False
        instance.post.side_effect = httpx.ConnectError("down")
        cls.return_value = instance
        with pytest.raises(DjangoUnreachable):
            await client.bootstrap(
                did="+1",
                edge_call_id="c",
                from_number="",
                sip_call_id="",
                direction="inbound",
            )


@pytest.mark.asyncio
async def test_bootstrap_success_unwraps_envelope():
    client = DjangoVoiceClient(_config())
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"success": True, "data": {"admitted": True}}
    with patch("httpx.AsyncClient") as cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = False
        instance.post = AsyncMock(return_value=response)
        cls.return_value = instance
        data = await client.bootstrap(
            did="+1",
            edge_call_id="c",
            from_number="",
            sip_call_id="",
            direction="inbound",
        )
    assert data["admitted"] is True
    headers = instance.post.await_args.kwargs["headers"]
    assert headers["X-Vokit-Internal-Token"] == "internal"


@pytest.mark.asyncio
async def test_get_transfer_status_gets_internal_endpoint():
    client = DjangoVoiceClient(_config())
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": {"ok": True, "status": "pending", "continue_call": True},
    }
    with patch("httpx.AsyncClient") as cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = False
        instance.get = AsyncMock(return_value=response)
        cls.return_value = instance
        data = await client.get_transfer_status(edge_call_id="edge-1")
    assert data["status"] == "pending"
    url = instance.get.await_args.args[0]
    assert url.endswith("/internal/telephony/v1/voice-session/transfer/status/")
    assert instance.get.await_args.kwargs["params"]["edge_call_id"] == "edge-1"


@pytest.mark.asyncio
async def test_poll_transfer_until_terminal_exits_on_non_pending():
    client = DjangoVoiceClient(_config())
    client.get_transfer_status = AsyncMock(
        side_effect=[
            {"status": "pending", "continue_call": True},
            {"status": "idle", "ok": False, "reason": "no_answer", "continue_call": True},
        ]
    )
    with patch("asyncio.sleep", new_callable=AsyncMock):
        data = await client.poll_transfer_until_terminal(edge_call_id="edge-1")
    assert data["reason"] == "no_answer"
    assert client.get_transfer_status.await_count == 2


@pytest.mark.asyncio
async def test_request_transfer_posts_internal_endpoint():
    client = DjangoVoiceClient(_config())
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": {"ok": True, "available": True, "status": "pending", "continue_call": True},
    }
    with patch("httpx.AsyncClient") as cls:
        instance = AsyncMock()
        instance.__aenter__.return_value = instance
        instance.__aexit__.return_value = False
        instance.post = AsyncMock(return_value=response)
        cls.return_value = instance
        data = await client.request_transfer(edge_call_id="edge-1")
    assert data["status"] == "pending"
    url = instance.post.await_args.args[0]
    assert url.endswith("/internal/telephony/v1/voice-session/transfer/")
    body = instance.post.await_args.kwargs["json"]
    assert body["edge_call_id"] == "edge-1"

