"""One inbound WebSocket = one Pipecat pipeline (OQ-037)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.frames.frames import (
    EndFrame,
    ErrorFrame,
    Frame,
    InputAudioRawFrame,
    OutputAudioRawFrame,
    TranscriptionFrame,
    TTSSpeakFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.workers.runner import WorkerRunner

from vokit_pipecat_voice.config import PipecatVoiceConfig
from vokit_pipecat_voice.django_client import DjangoUnreachable, DjangoVoiceClient
from vokit_pipecat_voice.knowledge.processor import KnowledgeRetrieveProcessor
from vokit_pipecat_voice.knowledge.tts_cache import (
    SkipPathTtsCacheCapture,
    SkipPathTtsCacheGate,
)
from vokit_pipecat_voice.pipeline.analyzers import build_vad_and_turn_analyzers
from vokit_pipecat_voice.pipeline.inbound_path import user_aggregator_params
from vokit_pipecat_voice.pipeline.inbound_tools import build_inbound_tools
from vokit_pipecat_voice.providers.mapper import (
    UnsupportedProviderError,
    build_pipeline_services,
)
from vokit_pipecat_voice.queued_websocket import QueuedWebSocket
from vokit_pipecat_voice.serializers.vokit_edge import (
    ULAW_FRAME_BYTES,
    VokitEdgeFrameSerializer,
)

logger = logging.getLogger(__name__)

# Wire contract stays 8 kHz μ-law (OQ-036). Official Pipecat telephony
# (Twilio/Plivo) sets audio_in_sample_rate=8000 so the serializer does not
# upsample 20 ms packets into empty PCM. TTS still runs at 24 kHz PCM;
# the serializer downsamples to 8 kHz μ-law. audio_out_10ms_chunks=2 matches
# the edge RTP pace (20 ms / 160 bytes).
# https://docs.pipecat.ai/pipecat/telephony/twilio-websockets
AUDIO_IN_SAMPLE_RATE = 8000
AUDIO_OUT_SAMPLE_RATE = 24000
AUDIO_OUT_10MS_CHUNKS = 2


class _EchoProbe(FrameProcessor):
    """PIPECAT_INBOUND_DIAG=1 loopback: echoes caller audio, skipping STT/LLM/TTS."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, InputAudioRawFrame) and direction == FrameDirection.DOWNSTREAM:
            await self.push_frame(
                OutputAudioRawFrame(
                    audio=frame.audio,
                    sample_rate=frame.sample_rate,
                    num_channels=frame.num_channels,
                ),
                direction,
            )
            return
        await self.push_frame(frame, direction)


class _UserTranscriptObserver(FrameProcessor):
    """Persist user transcripts without blocking the STT → LLM critical path.

    Interruption/barge-in still flows through the pipeline as
    ``InterruptionFrame`` from Cartesia turn-start; this observer must not
    delay pushing ``TranscriptionFrame`` downstream while Django HTTP runs.
    """

    def __init__(self, django: DjangoVoiceClient, edge_call_id: str) -> None:
        super().__init__()
        self._django = django
        self._edge_call_id = edge_call_id

    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame):
            text = (getattr(frame, "text", None) or "").strip()
            if text:
                logger.info("user transcript edge_call_id=%s text=%s", self._edge_call_id, text[:200])
                # Push first so LLM/TTS start immediately; persist in background.
                asyncio.create_task(
                    self._persist_user_turn(text),
                    name=f"vokit-persist-user-{self._edge_call_id}",
                )
        await self.push_frame(frame, direction)

    async def _persist_user_turn(self, text: str) -> None:
        try:
            result = await self._django.send_event(
                edge_call_id=self._edge_call_id,
                event_type="transcript_turn",
                role="user",
                text=text,
            )
        except DjangoUnreachable:
            logger.error("django unreachable on user turn — fail closed")
            await self.push_frame(EndFrame())
            return
        if result.get("continue_call") is False:
            await self.push_frame(EndFrame())


def _build_context(agent: dict[str, Any], tools=None) -> LLMContext:
    prompt = (
        (agent.get("resolved_system_prompt") or agent.get("system_prompt") or "").strip()
        or "You are a helpful inbound voice receptionist. Keep replies short and spoken."
    )
    greeting = (agent.get("welcome_greeting") or "").strip()
    messages: list[dict[str, str]] = [{"role": "system", "content": prompt}]
    if greeting:
        messages.append({"role": "assistant", "content": greeting})
    if tools:
        return LLMContext(messages, tools=ToolsSchema(standard_tools=tools))
    return LLMContext(messages)


async def run_inbound_pipeline(
    *,
    websocket: WebSocket | QueuedWebSocket,
    config: PipecatVoiceConfig,
    django: DjangoVoiceClient,
    bootstrap: dict[str, Any],
    start: dict[str, Any],
) -> None:
    edge_call_id = bootstrap.get("edge_call_id") or start.get("call_id") or ""
    agent = bootstrap.get("agent") or {}
    providers = bootstrap.get("providers") or {}
    timers = bootstrap.get("timers") or {}
    greeting = (agent.get("welcome_greeting") or "").strip()
    silence_timeout = int(timers.get("silence_timeout_seconds") or 0)
    max_duration = int(timers.get("max_call_duration_seconds") or 0)

    ended = asyncio.Event()
    end_reason = "stop"
    end_status = ""
    worker: PipelineWorker | None = None
    transfer_pending = False

    async def fail_closed(reason: str, status: str = "failed") -> None:
        nonlocal end_reason, end_status
        end_reason = reason
        end_status = status
        if ended.is_set():
            return
        ended.set()
        if worker is not None:
            try:
                await worker.cancel()
            except Exception:  # noqa: BLE001
                logger.exception("pipeline cancel after fail-closed failed")

    diagnostic = bool(config.inbound_diag)
    stt = tts = llm = None
    if not diagnostic:
        try:
            stt, tts, llm = build_pipeline_services(providers)
        except UnsupportedProviderError as exc:
            logger.error("provider mapper failed edge_call_id=%s: %s", edge_call_id, exc)
            try:
                await django.send_event(
                    edge_call_id=edge_call_id,
                    event_type="provider_failure",
                    reason=str(exc),
                )
            except DjangoUnreachable:
                pass
            try:
                await django.end_session(
                    edge_call_id=edge_call_id,
                    reason="provider_failure",
                    status="failed",
                )
            except DjangoUnreachable:
                pass
            await websocket.close(code=4403)
            return

    serializer = VokitEdgeFrameSerializer()
    # ONNX load is CPU-bound; keep it off the event loop so the WS pump
    # can keep draining edge μ-law.
    cartesia_turns = stt is not None and stt.__class__.__name__ == "CartesiaTurnsSTTService"
    if diagnostic:
        vad_analyzer = None
        turn_analyzer = None
    elif cartesia_turns:
        # ink-2 drives turn boundaries server-side (ExternalUserTurnStrategies).
        # Skip per-call Silero ONNX load — it was delaying greeting by seconds.
        # Deepgram / ElevenLabs still load VAD + Smart Turn below.
        vad_analyzer = None
        turn_analyzer = None
    else:
        vad_analyzer, turn_analyzer = await asyncio.to_thread(
            build_vad_and_turn_analyzers,
            AUDIO_IN_SAMPLE_RATE,
        )
    transport_params = FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        add_wav_header=False,
        serializer=serializer,
        audio_in_sample_rate=AUDIO_IN_SAMPLE_RATE,
        audio_out_sample_rate=AUDIO_OUT_SAMPLE_RATE,
        audio_out_10ms_chunks=AUDIO_OUT_10MS_CHUNKS,
        fixed_audio_packet_size=ULAW_FRAME_BYTES,
        audio_out_auto_silence=False,
        allowed_origins=list(config.allowed_origins),
        session_timeout=max_duration or None,
    )
    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=transport_params,
    )

    if diagnostic:
        logger.warning(
            "PIPECAT_INBOUND_DIAG=1 — echoing caller audio, skipping STT/LLM/TTS call_id=%s",
            edge_call_id,
        )
        pipeline = Pipeline([transport.input(), _EchoProbe(), transport.output()])
        user_aggregator = assistant_aggregator = observer = None
    else:
        async def _on_transfer_success() -> None:
            nonlocal end_reason, end_status, transfer_pending
            transfer_pending = True
            end_reason = "transferred"
            end_status = "completed"
            if worker is not None:
                await worker.queue_frame(EndFrame())

        inbound_tools = build_inbound_tools(
            django=django,
            edge_call_id=edge_call_id,
            transfer_spec=bootstrap.get("transfer") or {},
            on_transfer_success=_on_transfer_success,
        )
        register = getattr(llm, "register_function", None)
        if callable(register):
            for schema in inbound_tools:
                if schema.handler is not None:
                    register(schema.name, schema.handler)
        context = _build_context(agent, tools=inbound_tools or None)
        user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
            context,
            user_params=user_aggregator_params(stt, vad_analyzer, turn_analyzer),
        )

        @assistant_aggregator.event_handler("on_assistant_turn_stopped")
        async def _on_assistant_turn_stopped(aggregator, message):
            if message is None:
                return
            content = getattr(message, "content", None) or getattr(message, "text", None) or ""
            if not isinstance(content, str):
                content = str(content)
            content = content.strip()
            if not content:
                return
            try:
                result = await django.send_event(
                    edge_call_id=edge_call_id,
                    event_type="transcript_turn",
                    role="assistant",
                    text=content,
                )
                if result.get("continue_call") is False:
                    await fail_closed(str(result.get("reason") or "stop"), "completed")
            except DjangoUnreachable:
                await fail_closed("django_unreachable", "failed")

        observer = _UserTranscriptObserver(django, edge_call_id)
        retriever = KnowledgeRetrieveProcessor(
            knowledge=bootstrap.get("knowledge") or {},
            embedding=providers.get("embedding") if isinstance(providers, dict) else None,
            qdrant_url=config.qdrant_url,
        )
        tts_cfg = providers.get("tts") if isinstance(providers, dict) else None
        tts_voice = ""
        if isinstance(tts_cfg, dict):
            tts_voice = str(tts_cfg.get("voice_id") or tts_cfg.get("model") or "")
        tts_cache_gate = SkipPathTtsCacheGate(
            voice_id=tts_voice,
            sample_rate=AUDIO_OUT_SAMPLE_RATE,
        )
        tts_cache_capture = SkipPathTtsCacheCapture(tts_cache_gate)
        pipeline = Pipeline(
            [
                transport.input(),
                stt,
                observer,
                user_aggregator,
                retriever,
                llm,
                tts_cache_gate,
                tts,
                tts_cache_capture,
                transport.output(),
                assistant_aggregator,
            ]
        )
    params = PipelineParams(
        audio_in_sample_rate=AUDIO_IN_SAMPLE_RATE,
        audio_out_sample_rate=AUDIO_OUT_SAMPLE_RATE,
    )
    worker = PipelineWorker(
        pipeline,
        params=params,
        enable_rtvi=False,
        idle_timeout_secs=float(silence_timeout) if silence_timeout > 0 else None,
        cancel_on_idle_timeout=True,
    )

    @transport.event_handler("on_client_connected")
    async def _on_connected(transport, ws):
        if greeting and not diagnostic:
            # Greeting is already seeded into LLMContext; do not append again.
            await worker.queue_frame(TTSSpeakFrame(text=greeting, append_to_context=False))

    @transport.event_handler("on_client_disconnected")
    async def _on_disconnected(transport, ws):
        nonlocal end_reason
        if not ended.is_set():
            end_reason = "ws_disconnect"
            ended.set()
        if worker is not None:
            await worker.cancel()

    @transport.event_handler("on_session_timeout")
    async def _on_timeout(transport, ws):
        await fail_closed("max_duration", "completed")

    @worker.event_handler("on_idle_timeout")
    async def _on_idle_timeout(idle_worker):
        await fail_closed("silence_timeout", "completed")

    @worker.event_handler("on_pipeline_error")
    async def _on_pipeline_error(error_worker, frame: ErrorFrame):
        error_text = str(getattr(frame, "error", None) or frame)
        logger.error("pipeline provider error edge_call_id=%s: %s", edge_call_id, error_text)
        try:
            await django.send_event(
                edge_call_id=edge_call_id,
                event_type="provider_failure",
                reason=error_text[:500],
            )
        except DjangoUnreachable:
            logger.error("django unreachable reporting provider failure")
        await fail_closed("provider_failure", "failed")

    async def heartbeat_loop() -> None:
        interval = max(1.0, float(config.heartbeat_seconds))
        while not ended.is_set():
            await asyncio.sleep(interval)
            if ended.is_set():
                return
            try:
                result = await django.send_event(
                    edge_call_id=edge_call_id,
                    event_type="heartbeat",
                )
            except DjangoUnreachable:
                await fail_closed("django_unreachable", "failed")
                return
            if result.get("continue_call") is False:
                await fail_closed(str(result.get("reason") or "stop"), "completed")
                return

    heartbeat_task = asyncio.create_task(heartbeat_loop())
    runner = WorkerRunner(handle_sigint=False)
    try:
        await runner.add_workers(worker)
        await runner.run()
    except Exception:  # noqa: BLE001
        logger.exception("pipeline runner failed edge_call_id=%s", edge_call_id)
        end_reason = "provider_failure"
        end_status = "failed"
    finally:
        ended.set()
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        try:
            await django.end_session(
                edge_call_id=edge_call_id,
                reason=end_reason,
                status=end_status,
            )
        except DjangoUnreachable:
            logger.error(
                "django unreachable at end — fail closed already applied edge_call_id=%s",
                edge_call_id,
            )
        logger.info("call ended edge_call_id=%s reason=%s status=%s", edge_call_id, end_reason, end_status)
