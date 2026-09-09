"""
FastAPI media peer for vokit-sip-edge.

Path ``/sip/media`` matches the frozen Vokit WS contract. Edge is the client.
One WebSocket connection starts one pipeline (OQ-037).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from vokit_pipecat_voice.config import load_config
from vokit_pipecat_voice.django_client import DjangoUnreachable, DjangoVoiceClient
from vokit_pipecat_voice.pipeline.analyzers import preload_voice_models
from vokit_pipecat_voice.pipeline.session import run_inbound_pipeline
from vokit_pipecat_voice.queued_websocket import QueuedWebSocket

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

config = load_config()
django = DjangoVoiceClient(config)


def _preload_enabled() -> bool:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    return os.environ.get("PIPECAT_PRELOAD_MODELS", "1").strip().lower() not in {
        "0",
        "false",
        "no",
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    if _preload_enabled():
        logger.info("preloading Silero VAD and Smart Turn")
        try:
            await asyncio.to_thread(preload_voice_models, 8000)
            logger.info("voice models preloaded")
        except Exception:  # noqa: BLE001
            logger.exception("voice model preload failed; first call will load in a worker thread")
        logger.info("preloading FastEmbed query model")
        try:
            from vokit_pipecat_voice.knowledge.embed import preload_fastembed_model

            await asyncio.to_thread(preload_fastembed_model)
            logger.info("FastEmbed model preloaded")
        except Exception:  # noqa: BLE001
            logger.exception("FastEmbed preload failed; first retrieve will load the ONNX model")
        if config.qdrant_url:
            logger.info("warming Qdrant HTTP connection")
            try:
                from vokit_pipecat_voice.knowledge.retrieve import warmup_qdrant

                await warmup_qdrant(config.qdrant_url)
                logger.info("Qdrant HTTP connection warmed")
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Qdrant warmup failed; first retrieve may miss the 80 ms budget"
                )
    yield


app = FastAPI(title="vokit-pipecat-voice", version="0.1.0", lifespan=lifespan)
_cors_origins = list(config.allowed_origins) or [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "service": "vokit-pipecat-voice",
            "codec": "pcmu",
            "sample_rate": 8000,
        }
    )


def _token_ok(provided: str | None) -> bool:
    expected = config.media_ws_token
    if not expected or not provided:
        return False
    return secrets.compare_digest(provided, expected)


async def _wait_for_start(
    websocket: WebSocket | QueuedWebSocket, timeout: float = 20.0
) -> dict[str, Any] | None:
    async def _read() -> dict[str, Any] | None:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                return None
            text = message.get("text")
            if text:
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict) and payload.get("type") == "start":
                    return payload
            # Binary before start is dropped (edge sends start first). After
            # start, remaining queued frames stay for the pipeline.

    try:
        return await asyncio.wait_for(_read(), timeout=timeout)
    except TimeoutError:
        logger.warning("media ws timed out waiting for start")
        return None
    except WebSocketDisconnect:
        return None


async def _echo_until_close(websocket: WebSocket | QueuedWebSocket) -> None:
    """Outbound / non-AI path — preserve edge smoke behavior (μ-law echo)."""
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                return
            if message.get("bytes") is not None:
                await websocket.send_bytes(message["bytes"])
            text = message.get("text")
            if text:
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict) and payload.get("type") == "stop":
                    return
    except WebSocketDisconnect:
        return


@app.websocket("/sip/media")
async def sip_media(websocket: WebSocket) -> None:
    token = websocket.query_params.get("media_token")
    if not _token_ok(token):
        logger.warning("media ws rejected: invalid or missing media_token")
        await websocket.close(code=4401)
        return

    await websocket.accept()
    qs_call_id = websocket.query_params.get("call_id") or ""
    logger.info("media ws accepted call_id=%s", qs_call_id)

    queued = QueuedWebSocket(websocket)
    queued.start()
    try:
        start = await _wait_for_start(queued)
        if start is None:
            logger.warning("media ws closed before start call_id=%s", qs_call_id)
            try:
                await websocket.close()
            except Exception:  # noqa: BLE001
                pass
            return

        await _run_after_start(
            websocket=websocket,
            queued=queued,
            start=start,
            qs_call_id=qs_call_id,
        )
    finally:
        logger.info("media ws closed call_id=%s", qs_call_id)
        await queued.aclose()


async def _run_after_start(
    *,
    websocket: WebSocket,
    queued: QueuedWebSocket,
    start: dict[str, Any],
    qs_call_id: str,
) -> None:
    direction = (start.get("direction") or "inbound").strip().lower()
    call_id = start.get("call_id") or qs_call_id
    did = start.get("to") or websocket.query_params.get("to") or ""
    from_number = start.get("from") or websocket.query_params.get("from") or ""
    sip_call_id = start.get("sip_call_id") or ""

    if direction != "inbound":
        logger.info("outbound/non-ai echo path call_id=%s", call_id)
        await _echo_until_close(queued)
        return

    try:
        bootstrap = await django.bootstrap(
            did=did,
            edge_call_id=str(call_id),
            from_number=str(from_number),
            sip_call_id=str(sip_call_id),
            direction=direction,
        )
    except DjangoUnreachable:
        logger.error("django unreachable at bootstrap call_id=%s — fail closed", call_id)
        await websocket.close(code=4403)
        return

    if not bootstrap.get("admitted"):
        logger.warning(
            "bootstrap not admitted call_id=%s reason=%s",
            call_id,
            bootstrap.get("reject_reason"),
        )
        await websocket.close(code=4403)
        return

    logger.info(
        "media ws handing off to pipeline call_id=%s queued_frames=%s",
        call_id,
        queued.pending,
    )
    await run_inbound_pipeline(
        websocket=queued,
        config=config,
        django=django,
        bootstrap=bootstrap,
        start=start,
    )


@app.post("/training/webrtc/offer")
async def training_webrtc_offer(payload: dict[str, Any], background_tasks: BackgroundTasks):
    """SmallWebRTC signaling for Developer Training (beside /sip/media)."""
    session_token = ""
    request_data = payload.get("request_data") or payload.get("requestData") or {}
    if isinstance(request_data, dict):
        session_token = str(request_data.get("session_token") or "")
    if not session_token:
        session_token = str(payload.get("session_token") or "")
    if not session_token:
        return JSONResponse({"detail": "session_token required"}, status_code=400)

    try:
        from pipecat.transports.base_transport import TransportParams
        from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
        from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
    except ImportError as exc:
        logger.exception("SmallWebRTC import failed")
        return JSONResponse(
            {"detail": f"SmallWebRTC is not available: {exc}"},
            status_code=501,
        )

    try:
        bootstrap = await django.training_bootstrap(session_token=session_token)
    except DjangoUnreachable:
        return JSONResponse({"detail": "django unreachable"}, status_code=503)

    if not bootstrap.get("admitted"):
        return JSONResponse({"detail": "training session not admitted"}, status_code=403)

    connection = SmallWebRTCConnection(
        ice_servers=["stun:stun.l.google.com:19302"],
    )
    await connection.initialize(sdp=payload.get("sdp") or "", type=payload.get("type") or "offer")

    async def _run() -> None:
        from vokit_pipecat_voice.pipeline.training import (
            TRAINING_AUDIO_IN_SAMPLE_RATE,
            TRAINING_AUDIO_OUT_SAMPLE_RATE,
            run_training_pipeline,
        )

        transport = SmallWebRTCTransport(
            webrtc_connection=connection,
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                audio_in_sample_rate=TRAINING_AUDIO_IN_SAMPLE_RATE,
                audio_out_sample_rate=TRAINING_AUDIO_OUT_SAMPLE_RATE,
            ),
        )
        await run_training_pipeline(
            transport=transport,
            config=config,
            django=django,
            bootstrap=bootstrap,
            session_token=session_token,
        )

    background_tasks.add_task(_run)
    return connection.get_answer()

