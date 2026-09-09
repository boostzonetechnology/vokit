"""Queued WebSocket keeps inbound media flowing during Django bootstrap."""
from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

import vokit_pipecat_voice.app as app_mod
from vokit_pipecat_voice.queued_websocket import QueuedWebSocket


class _FakeInner:
    def __init__(self) -> None:
        self.incoming: asyncio.Queue[dict] = asyncio.Queue()
        self.sent: list[bytes] = []

    async def receive(self) -> dict:
        return await self.incoming.get()

    async def send_bytes(self, data: bytes) -> None:
        self.sent.append(data)


class _FlowControlledInner:
    """Mimics uvicorn's WebSocketsSansIOProtocol read-side flow control.

    Real uvicorn (websockets_sansio_impl.py) pauses transport reads after
    every inbound message and only resumes inside receive() once its queue
    empties. A receive() that gets cancelled mid-flight can consume the
    queued item without ever reaching the resume check, leaving reads paused
    forever (calls 9ec2204d / d1419411). This fake reproduces that exact
    invariant so a regression can prove QueuedWebSocket never cancels an
    in-flight receive().
    """

    def __init__(self) -> None:
        self.queue: asyncio.Queue[dict] = asyncio.Queue()
        self.read_paused = False
        self.resume_calls = 0
        self.sent: list[bytes] = []

    def push(self, message: dict) -> None:
        self.queue.put_nowait(message)
        if not self.read_paused:
            self.read_paused = True

    async def receive(self) -> dict:
        message = await self.queue.get()
        if self.read_paused and self.queue.empty():
            self.read_paused = False
            self.resume_calls += 1
        return message

    async def send_bytes(self, data: bytes) -> None:
        await asyncio.sleep(0.01)
        self.sent.append(data)


@pytest.mark.asyncio
async def test_queued_websocket_buffers_while_consumer_is_busy():
    inner = _FakeInner()
    queued = QueuedWebSocket(inner)  # type: ignore[arg-type]
    queued.start()
    try:
        await inner.incoming.put({"type": "websocket.receive", "bytes": b"\x00" * 160})
        await inner.incoming.put({"type": "websocket.receive", "bytes": b"\x01" * 160})
        await asyncio.sleep(0.05)
        assert queued.pending >= 2
        first = await queued.receive()
        second = await queued.receive()
        assert first["bytes"] == b"\x00" * 160
        assert second["bytes"] == b"\x01" * 160
    finally:
        await queued.aclose()


@pytest.mark.asyncio
async def test_queued_websocket_skips_empty_receive_and_keeps_audio():
    inner = _FakeInner()
    queued = QueuedWebSocket(inner)  # type: ignore[arg-type]
    queued.start()
    try:
        await inner.incoming.put({"type": "websocket.receive"})
        await inner.incoming.put({"type": "websocket.receive", "bytes": None, "text": None})
        await inner.incoming.put({"type": "websocket.receive", "bytes": b"\x02" * 160})
        await asyncio.sleep(0.05)
        message = await queued.receive()
        assert message["bytes"] == b"\x02" * 160
        assert queued.pending == 0
    finally:
        await queued.aclose()


def _set_media_token(monkeypatch, token: str) -> None:
    monkeypatch.setattr(app_mod, "config", replace(app_mod.config, media_ws_token=token))


def test_inbound_audio_is_kept_during_bootstrap(monkeypatch):
    _set_media_token(monkeypatch, "tok")
    captured: list[bytes] = []
    bootstrap_started = threading.Event()
    pipeline_done = threading.Event()

    async def slow_bootstrap(**kwargs):
        bootstrap_started.set()
        # Stay busy so the pump must buffer frames without a pipeline consumer.
        await asyncio.sleep(0.15)
        return {
            "admitted": True,
            "edge_call_id": "in-buf",
            "agent": {"welcome_greeting": "Hi"},
            "providers": {},
            "timers": {},
        }

    async def capture_pipeline(*, websocket, **kwargs):
        try:
            for _ in range(3):
                message = await websocket.receive()
                if message.get("bytes") is not None:
                    captured.append(message["bytes"])
        finally:
            pipeline_done.set()

    monkeypatch.setattr(app_mod.django, "bootstrap", slow_bootstrap)
    monkeypatch.setattr(app_mod, "run_inbound_pipeline", capture_pipeline)
    client = TestClient(app_mod.app)
    with client.websocket_connect("/sip/media?media_token=tok") as ws:
        ws.send_text(
            json.dumps(
                {
                    "type": "start",
                    "call_id": "in-buf",
                    "from": "+1",
                    "to": "+2",
                    "direction": "inbound",
                }
            )
        )
        assert bootstrap_started.wait(timeout=2.0)
        ws.send_bytes(b"\x10" * 160)
        ws.send_bytes(b"\x20" * 160)
        ws.send_bytes(b"\x30" * 160)
        assert pipeline_done.wait(timeout=2.0)
        ws.close()

    assert captured == [b"\x10" * 160, b"\x20" * 160, b"\x30" * 160]


def test_inbound_audio_sent_immediately_after_start_is_kept(monkeypatch):
    """Edge sends start then RTP immediately; pump must keep those frames."""
    _set_media_token(monkeypatch, "tok")
    captured: list[bytes] = []
    pipeline_done = threading.Event()

    async def slow_bootstrap(**kwargs):
        await asyncio.sleep(0.15)
        return {
            "admitted": True,
            "edge_call_id": "in-now",
            "agent": {"welcome_greeting": "Hi"},
            "providers": {},
            "timers": {},
        }

    async def capture_pipeline(*, websocket, **kwargs):
        try:
            for _ in range(3):
                message = await websocket.receive()
                if message.get("bytes") is not None:
                    captured.append(message["bytes"])
        finally:
            pipeline_done.set()

    monkeypatch.setattr(app_mod.django, "bootstrap", slow_bootstrap)
    monkeypatch.setattr(app_mod, "run_inbound_pipeline", capture_pipeline)
    client = TestClient(app_mod.app)
    with client.websocket_connect("/sip/media?media_token=tok") as ws:
        ws.send_text(
            json.dumps(
                {
                    "type": "start",
                    "call_id": "in-now",
                    "from": "+1",
                    "to": "+2",
                    "direction": "inbound",
                }
            )
        )
        ws.send_bytes(b"\x11" * 160)
        ws.send_bytes(b"\x22" * 160)
        ws.send_bytes(b"\x33" * 160)
        assert pipeline_done.wait(timeout=2.0)
        ws.close()

    assert captured == [b"\x11" * 160, b"\x22" * 160, b"\x33" * 160]


@pytest.mark.asyncio
async def test_concurrent_tts_sends_never_stall_or_desync_read_pause():
    """Regression for calls 9ec2204d / d1419411.

    Cancelling an in-flight receive() to interleave a TTS send can leave
    uvicorn's read_paused stuck True forever, permanently freezing inbound
    audio while sends keep working. QueuedWebSocket must let every receive()
    it starts run to completion, so read_paused always gets cleared.
    """
    inner = _FlowControlledInner()
    queued = QueuedWebSocket(inner)  # type: ignore[arg-type]
    queued.start()
    try:
        # Fire TTS-style sends concurrently with inbound frames arriving,
        # the same overlap that triggered the freeze on a real call.
        senders = [asyncio.create_task(queued.send_bytes(bytes([i]) * 160)) for i in range(8)]
        received = []
        for i in range(6):
            inner.push({"type": "websocket.receive", "bytes": bytes([0xA0 + i]) * 160})
            await asyncio.sleep(0.002)
            received.append(await queued.receive())
        await asyncio.gather(*senders)

        assert [message["bytes"][0] for message in received] == [0xA0 + i for i in range(6)]
        assert len(inner.sent) == 8
        # Every push must have been drained AND resumed reads — if a
        # receive() had been cancelled mid-flight this would stay True/short.
        assert inner.read_paused is False
        assert inner.resume_calls == 6
    finally:
        await queued.aclose()
