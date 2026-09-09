"""Serializer contract tests for the Vokit edge wire format."""
from __future__ import annotations

import json

import pytest

from pipecat.frames.frames import (
    EndFrame,
    InputAudioRawFrame,
    InputTransportMessageFrame,
    InterruptionFrame,
    OutputAudioRawFrame,
    StartFrame,
)

from vokit_pipecat_voice.serializers.vokit_edge import (
    ULAW_FRAME_BYTES,
    VokitEdgeFrameSerializer,
)


@pytest.mark.asyncio
async def test_deserialize_start_and_stop():
    serializer = VokitEdgeFrameSerializer()
    start = await serializer.deserialize(
        json.dumps(
            {
                "type": "start",
                "call_id": "abc",
                "from": "+1",
                "to": "+2",
                "direction": "inbound",
            }
        )
    )
    assert isinstance(start, InputTransportMessageFrame)
    stop = await serializer.deserialize(json.dumps({"type": "stop", "reason": "call_ended"}))
    assert isinstance(stop, EndFrame)


@pytest.mark.asyncio
async def test_interruption_emits_clear_json_substring():
    serializer = VokitEdgeFrameSerializer()
    payload = await serializer.serialize(InterruptionFrame())
    assert isinstance(payload, str)
    assert '"clear"' in payload
    parsed = json.loads(payload)
    assert parsed["type"] == "clear"


@pytest.mark.asyncio
async def test_ulaw_round_trip_8khz():
    serializer = VokitEdgeFrameSerializer()
    ulaw = bytes([0xFF]) * ULAW_FRAME_BYTES
    frame = await serializer.deserialize(ulaw)
    assert isinstance(frame, InputAudioRawFrame)
    assert frame.sample_rate == 8000
    assert frame.num_channels == 1
    assert len(frame.audio) > 0

    out = OutputAudioRawFrame(
        audio=frame.audio,
        sample_rate=8000,
        num_channels=1,
    )
    encoded = await serializer.serialize(out)
    assert isinstance(encoded, (bytes, bytearray))
    assert len(encoded) > 0


@pytest.mark.asyncio
async def test_serialize_resamples_24khz_pcm_to_8khz_ulaw():
    """24 kHz TTS PCM must be downsampled; otherwise the edge plays slow-motion."""
    serializer = VokitEdgeFrameSerializer()
    duration_ms = 1000
    samples = int(24000 * duration_ms / 1000)
    pcm_24k = b"\x00\x10" * samples
    encoded = await serializer.serialize(
        OutputAudioRawFrame(audio=pcm_24k, sample_rate=24000, num_channels=1)
    )
    assert isinstance(encoded, (bytes, bytearray))
    expected_ulaw = int(8000 * duration_ms / 1000)
    # Stream resampler may add a small delay; duration must stay ~1x, not ~3x.
    assert 0.7 * expected_ulaw < len(encoded) < 1.4 * expected_ulaw


@pytest.mark.asyncio
async def test_deserialize_upsamples_8k_ulaw_to_pipeline_16k():
    serializer = VokitEdgeFrameSerializer()
    await serializer.setup(StartFrame(audio_in_sample_rate=16000, audio_out_sample_rate=24000))
    pcm = bytearray()
    for _ in range(50):
        frame = await serializer.deserialize(bytes([0xFF]) * ULAW_FRAME_BYTES)
        if isinstance(frame, InputAudioRawFrame):
            assert frame.sample_rate == 16000
            pcm.extend(frame.audio)
    # 1 s of 16 kHz PCM16 is 32000 bytes; stream resampler may trim the edges.
    assert 20000 < len(pcm) < 45000
