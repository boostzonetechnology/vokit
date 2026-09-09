"""Keep reading the media WebSocket while Django bootstrap and model load run.

Edge sends μ-law as soon as RTP starts. If nobody calls ``receive()``, the
inbound sender backpressures and caller audio never reaches STT.

Pipecat's FastAPI iterator stops forever on any message that has neither
``bytes`` nor ``text``. The pump therefore drops empty/unknown ASGI events
instead of forwarding them.

Concurrency contract (calls ``9ec2204d`` / ``d1419411``, inbound froze the
instant TTS started writing): uvicorn's ``WebSocketsSansIOProtocol``
(``uvicorn/protocols/websockets/websockets_sansio_impl.py``) pauses the
transport's read side after every inbound message and only resumes it inside
``receive()`` once its internal queue is drained:

    def send_receive_event_to_app(self):
        self.queue.put_nowait(...)
        if not self.read_paused:
            self.read_paused = True
            self.transport.pause_reading()

    async def receive(self):
        message = await self.queue.get()
        if self.read_paused and self.queue.empty():
            self.read_paused = False
            self.transport.resume_reading()
        return message

A ``receive()`` call that is cancelled mid-flight (e.g. to interleave an
outbound TTS write on the same task) can skip the ``resume_reading()`` line
even though the queued frame was consumed, leaving ``read_paused`` stuck
``True`` forever — uvicorn then never reads more bytes from the OS socket for
that connection again, even though sends keep working. A prior version of
this module did exactly that (cancel-and-recreate the receive task whenever a
send was ready) and reproduced the freeze.

The fix: never cancel an in-flight ``receive()``. One dedicated task loops
``receive()`` to completion every time and only that task drains the queue.
Outbound sends go straight through to the real socket from whatever task
calls them — this is the same concurrent-receive/independent-send pattern
Pipecat's own ``FastAPIWebsocketInputTransport``/``FastAPIWebsocketOutputTransport``
use with a bare ``WebSocket``, and it is safe.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


def _normalize_asgi_message(message: dict[str, Any]) -> dict[str, Any] | None:
    msg_type = message.get("type")
    if msg_type == "websocket.disconnect":
        return {"type": "websocket.disconnect", "code": message.get("code", 1000)}
    if msg_type != "websocket.receive":
        logger.info("media ws pump skipped type=%s", msg_type)
        return None
    data = message.get("bytes")
    if data is not None:
        return {"type": "websocket.receive", "bytes": data}
    text = message.get("text")
    if text is not None:
        return {"type": "websocket.receive", "text": text}
    logger.info("media ws pump skipped empty receive")
    return None


class QueuedWebSocket:
    """Duck-types FastAPI ``WebSocket``; ``receive()`` is served from a pump task.

    Sends are NOT routed through this class — they fall through
    ``__getattr__`` straight to the real WebSocket, on whatever task calls
    them, concurrently with the receive pump. See module docstring for why
    that is safe and why cancelling the pump's ``receive()`` is not.
    """

    def __init__(self, websocket: WebSocket) -> None:
        self._inner = websocket
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._pump_task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._pump_task is None:
            self._pump_task = asyncio.create_task(self._pump(), name="vokit-media-ws-pump")

    async def aclose(self) -> None:
        task = self._pump_task
        self._pump_task = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @property
    def pending(self) -> int:
        return self._queue.qsize()

    async def receive(self) -> dict[str, Any]:
        return await self._queue.get()

    async def receive_bytes(self) -> bytes:
        while True:
            message = await self.receive()
            if message.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect(message.get("code", 1000))
            data = message.get("bytes")
            if data is not None:
                return data

    async def receive_text(self) -> str:
        while True:
            message = await self.receive()
            if message.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect(message.get("code", 1000))
            text = message.get("text")
            if text is not None:
                return text

    async def receive_json(self, mode: str = "text") -> Any:
        import json

        if mode == "binary":
            return json.loads(await self.receive_bytes())
        return json.loads(await self.receive_text())

    async def iter_bytes(self) -> AsyncIterator[bytes]:
        while True:
            yield await self.receive_bytes()

    async def iter_text(self) -> AsyncIterator[str]:
        while True:
            yield await self.receive_text()

    async def _pump(self) -> None:
        try:
            while True:
                try:
                    raw = await self._inner.receive()
                except WebSocketDisconnect as exc:
                    await self._queue.put(
                        {"type": "websocket.disconnect", "code": getattr(exc, "code", 1000)}
                    )
                    logger.info("media ws pump stopped reason=disconnect")
                    return
                message = _normalize_asgi_message(raw)
                if message is None:
                    continue
                await self._queue.put(message)
                if message.get("type") == "websocket.disconnect":
                    logger.info("media ws pump stopped reason=disconnect")
                    return
        except asyncio.CancelledError:
            logger.info("media ws pump stopped reason=cancel")
            raise
        except Exception:
            logger.exception("media ws pump failed")
            await self._queue.put({"type": "websocket.disconnect", "code": 1011})

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)
