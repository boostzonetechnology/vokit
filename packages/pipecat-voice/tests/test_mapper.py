"""Provider mapper — consumes Django snapshot, does not store config."""
from __future__ import annotations

import pytest

from pipecat.services.tts_service import TextAggregationMode

from vokit_pipecat_voice.providers.mapper import (
    UnsupportedProviderError,
    build_stt,
    build_tts,
    build_llm,
)


def test_unknown_stt_fails_closed():
    with pytest.raises(UnsupportedProviderError, match="Unsupported STT"):
        build_stt({"provider_code": "madeup", "api_key": "k", "model": "x"})


def test_unknown_llm_fails_closed():
    with pytest.raises(UnsupportedProviderError, match="Unsupported LLM"):
        build_llm({"provider_code": "madeup", "api_key": "k", "model": "x"})


def test_known_stt_constructs_from_django_snapshot():
    stt = build_stt(
        {
            "provider_code": "deepgram",
            "api_key": "test-key",
            "model": "nova-3",
            "language": "en",
        }
    )
    assert stt is not None
    assert stt.__class__.__name__ == "DeepgramSTTService"
    assert getattr(stt, "_encoding", None) == "linear16"


def test_cartesia_ink2_uses_turns_stt_service():
    stt = build_stt(
        {
            "provider_code": "cartesia",
            "api_key": "test-key",
            "model": "ink-2",
            "language": "en",
        }
    )
    assert stt.__class__.__name__ == "CartesiaTurnsSTTService"


def test_cartesia_whisper_uses_v1_stt_service():
    stt = build_stt(
        {
            "provider_code": "cartesia",
            "api_key": "test-key",
            "model": "ink-whisper",
            "language": "en",
        }
    )
    assert stt.__class__.__name__ == "CartesiaSTTService"
    assert getattr(stt, "_encoding", None) == "pcm_s16le"


def test_cartesia_tts_sentence_with_zero_buffer_delay():
    """SENTENCE + buffer 0: natural speech, no 3s Cartesia managed wait."""
    from pipecat.services.cartesia.tts import GenerationConfig

    tts = build_tts(
        {
            "provider_code": "cartesia",
            "api_key": "test-key",
            "model": "sonic-3.5",
            "voice_id": "voice-123",
            "language": "en",
        }
    )
    assert tts.__class__.__name__ == "CartesiaTTSService"
    assert getattr(tts, "_text_aggregation_mode") == TextAggregationMode.SENTENCE
    assert getattr(tts, "_max_buffer_delay_ms") == 0
    gen = getattr(tts, "_settings").generation_config
    assert isinstance(gen, GenerationConfig)
    assert gen.speed == 1.15


def test_deepgram_tts_uses_sentence_aggregation():
    tts = build_tts(
        {
            "provider_code": "deepgram",
            "api_key": "test-key",
            "voice_id": "aura-2-thalia-en",
        }
    )
    assert tts.__class__.__name__ == "DeepgramTTSService"
    assert getattr(tts, "_text_aggregation_mode") == TextAggregationMode.SENTENCE


def test_elevenlabs_tts_uses_sentence_aggregation():
    tts = build_tts(
        {
            "provider_code": "elevenlabs",
            "api_key": "test-key",
            "model": "eleven_flash_v2_5",
            "voice_id": "voice-abc",
            "language": "en",
        }
    )
    assert tts.__class__.__name__ == "ElevenLabsTTSService"
    assert getattr(tts, "_text_aggregation_mode") == TextAggregationMode.SENTENCE
    assert getattr(tts, "_auto_mode") is True
