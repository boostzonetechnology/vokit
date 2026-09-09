"""
Vokit edge media serializer — existing WS contract, not Twilio Media Streams.

Wire format (packages/vokit-sip-edge/src/media/bridge.rs):
- JSON text ``start`` / ``stop``
- Binary G.711 μ-law (typically 160 bytes / 20 ms @ 8 kHz)
- Text containing ``"clear"`` resets edge RTP pacing (barge-in)

Verified against current pipecat-ai FrameSerializer (serialize / deserialize /
setup). FrameSerializerType is not required on this pin.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from pipecat.audio.utils import create_stream_resampler, pcm_to_ulaw, ulaw_to_pcm
from pipecat.frames.frames import (
    AudioRawFrame,
    EndFrame,
    Frame,
    InputAudioRawFrame,
    InputTransportMessageFrame,
    InterruptionFrame,
    StartFrame,
)
from pipecat.serializers.base_serializer import FrameSerializer

logger = logging.getLogger(__name__)

VOKIT_SAMPLE_RATE = 8000
ULAW_FRAME_BYTES = 160


class VokitEdgeFrameSerializer(FrameSerializer):
    """Pipecat ↔ vokit-sip-edge μ-law WebSocket adapter (OQ-031, OQ-036)."""

    class InputParams(FrameSerializer.InputParams):
        # None → use StartFrame.audio_in_sample_rate (typically 16 kHz STT/VAD).
        sample_rate: int | None = None
        # Telephony packets have irregular gaps; clearing the stream resampler
        # after 0.2s (Pipecat default) drops audio and sounds choppy.
        resampler_clear_after_secs: float | None = None

    def __init__(
        self,
        params: InputParams | None = None,
        *,
        sample_rate: int = VOKIT_SAMPLE_RATE,
    ) -> None:
        params = params or VokitEdgeFrameSerializer.InputParams()
        super().__init__(params)
        self._params: VokitEdgeFrameSerializer.InputParams = params
        self._wire_sample_rate = sample_rate
        self._pipeline_sample_rate = VOKIT_SAMPLE_RATE
        self._input_resampler = create_stream_resampler(
            clear_after_secs=self._params.resampler_clear_after_secs,
        )
        self._output_resampler = create_stream_resampler(
            clear_after_secs=self._params.resampler_clear_after_secs,
        )
        self.start_message: dict[str, Any] | None = None

    async def setup(self, frame: StartFrame) -> None:
        # Inbound pipeline rate (STT/VAD). Outbound uses each frame.sample_rate
        # so 24 kHz TTS PCM is resampled to 8 kHz μ-law (Twilio serializer pattern).
        self._pipeline_sample_rate = (
            self._params.sample_rate or frame.audio_in_sample_rate or VOKIT_SAMPLE_RATE
        )

    async def serialize(self, frame: Frame) -> str | bytes | None:
        if isinstance(frame, InterruptionFrame):
            # Edge matches substring '"clear"' (bridge.rs).
            return json.dumps({"type": "clear"})
        if isinstance(frame, AudioRawFrame):
            source_rate = frame.sample_rate or self._pipeline_sample_rate
            serialized = await pcm_to_ulaw(
                frame.audio,
                source_rate,
                self._wire_sample_rate,
                self._output_resampler,
            )
            if serialized is None or len(serialized) == 0:
                return None
            return bytes(serialized)
        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        if isinstance(data, bytes):
            return await self._deserialize_ulaw(data)
        if not isinstance(data, str):
            return None
        try:
            message = json.loads(data)
        except json.JSONDecodeError:
            if '"clear"' in data:
                return None
            logger.warning("vokit serializer ignored non-json text")
            return None
        if not isinstance(message, dict):
            return None
        msg_type = message.get("type")
        if msg_type == "start":
            self.start_message = message
            return InputTransportMessageFrame(message=message)
        if msg_type == "stop":
            return EndFrame()
        return None

    async def _deserialize_ulaw(self, payload: bytes) -> InputAudioRawFrame | None:
        if not payload:
            return None
        pcm = await ulaw_to_pcm(
            payload,
            self._wire_sample_rate,
            self._pipeline_sample_rate,
            self._input_resampler,
        )
        if pcm is None or len(pcm) == 0:
            return None
        return InputAudioRawFrame(
            audio=bytes(pcm),
            num_channels=1,
            sample_rate=self._pipeline_sample_rate,
        )
