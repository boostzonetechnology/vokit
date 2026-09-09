"""Cartesia vs Deepgram turn-strategy wiring."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pipecat.turns.user_turn_strategies import ExternalUserTurnStrategies, UserTurnStrategies

from vokit_pipecat_voice.pipeline.inbound_path import pcm16_rms, user_aggregator_params
from vokit_pipecat_voice.serializers.vokit_edge import ULAW_FRAME_BYTES, VokitEdgeFrameSerializer


class CartesiaTurnsSTTService:
    pass


class DeepgramSTTService:
    pass


def test_cartesia_ink2_uses_external_turn_strategies():
    params = user_aggregator_params(CartesiaTurnsSTTService(), MagicMock(), None)
    assert isinstance(params.user_turn_strategies, ExternalUserTurnStrategies)


def test_cartesia_ink2_allows_vad_none():
    """Greeting cold-start skip: Cartesia turns do not require Silero VAD."""
    params = user_aggregator_params(CartesiaTurnsSTTService(), None, None)
    assert params.vad_analyzer is None
    assert isinstance(params.user_turn_strategies, ExternalUserTurnStrategies)


def test_deepgram_keeps_vad_smart_turn_strategies():
    params = user_aggregator_params(DeepgramSTTService(), MagicMock(), MagicMock())
    assert isinstance(params.user_turn_strategies, UserTurnStrategies)
    assert not isinstance(params.user_turn_strategies, ExternalUserTurnStrategies)


def test_pcm16_rms_silence_near_zero():
    assert pcm16_rms(b"\x00\x00" * 160) == 0.0
    loud = b"\x00\x40" * 160
    assert pcm16_rms(loud) > 1000


@pytest.mark.asyncio
async def test_itu_ulaw_silence_is_0xff_not_a_decoder_bug():
    """PCMU silence is 0xFF; audioop.ulaw2lin (Pipecat) decodes it to PCM 0."""
    import audioop

    pcm = audioop.ulaw2lin(bytes([0xFF]) * ULAW_FRAME_BYTES, 2)
    assert pcm16_rms(pcm) == 0.0
    loud_ulaw = audioop.lin2ulaw(b"\x00\x40" * ULAW_FRAME_BYTES, 2)
    assert pcm16_rms(audioop.ulaw2lin(loud_ulaw, 2)) > 500


@pytest.mark.asyncio
async def test_serializer_preserves_non_silent_ulaw_energy():
    import audioop

    serializer = VokitEdgeFrameSerializer()
    speech = audioop.lin2ulaw(b"\x00\x40" * ULAW_FRAME_BYTES, 2)
    frame = await serializer.deserialize(speech)
    assert frame is not None
    assert pcm16_rms(frame.audio) > 500
    assert frame.sample_rate == 8000
    assert frame.num_channels == 1
    assert frame.audio != b"\x00\x00" * ULAW_FRAME_BYTES
