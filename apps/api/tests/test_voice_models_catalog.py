from __future__ import annotations

from unittest.mock import patch

import pytest

from providers.voice.models_catalog import list_provider_models
from shared_kernel.errors import DomainError


def test_openai_llm_models_normalize() -> None:
    with patch(
        "providers.voice.models_catalog.vendor_get",
        return_value={
            "data": [
                {"id": "gpt-4o"},
                {"id": "gpt-4o-mini"},
                {"id": "whisper-1"},
                {"id": "dall-e-3"},
            ]
        },
    ):
        payload = list_provider_models("openai", "llm", "sk-test")
    assert payload["provider"] == "openai"
    assert payload["capability"] == "llm"
    assert [row["id"] for row in payload["models"]] == ["gpt-4o", "gpt-4o-mini"]


def test_grok_filters_non_chat_models() -> None:
    with patch(
        "providers.voice.models_catalog.vendor_get",
        return_value={
            "data": [
                {"id": "grok-3"},
                {"id": "grok-2-image-1212"},
                {"id": "grok-2-vision-1212"},
                {"id": "other-model"},
            ]
        },
    ):
        payload = list_provider_models("grok", "llm", "xai-test")
    assert [row["id"] for row in payload["models"]] == ["grok-3"]


def test_cartesia_returns_documented_models_not_voices() -> None:
    with patch(
        "providers.voice.models_catalog.vendor_get",
        return_value={"data": [{"id": "voice-should-not-appear", "name": "Ava"}]},
    ) as probe:
        stt = list_provider_models("cartesia", "stt", "ck-test")
        tts = list_provider_models("cartesia", "tts", "ck-test")
    assert probe.call_count == 2
    assert "voices" in probe.call_args.args[0]
    assert [row["id"] for row in stt["models"]] == ["ink-2", "ink-whisper"]
    assert "sonic-3.6" in [row["id"] for row in tts["models"]]
    assert all(row["id"] != "voice-should-not-appear" for row in tts["models"])


def test_elevenlabs_splits_tts_and_stt() -> None:
    body = [
        {
            "model_id": "eleven_multilingual_v2",
            "name": "Multilingual v2",
            "can_do_text_to_speech": True,
        },
        {
            "model_id": "scribe_v1",
            "name": "Scribe v1",
            "can_do_text_to_speech": False,
            "can_do_speech_to_text": True,
        },
    ]
    with patch("providers.voice.models_catalog.vendor_get", return_value=body):
        tts = list_provider_models("elevenlabs", "tts", "el-test")
        stt = list_provider_models("elevenlabs", "stt", "el-test")
    assert [row["id"] for row in tts["models"]] == ["eleven_multilingual_v2"]
    assert [row["id"] for row in stt["models"]] == ["scribe_v1"]


def test_missing_key_fails_closed() -> None:
    with pytest.raises(DomainError) as exc:
        list_provider_models("openai", "llm", "  ")
    assert exc.value.code == "secret_missing"


def test_invalid_capability() -> None:
    with pytest.raises(DomainError) as exc:
        list_provider_models("openai", "embedding", "sk-test")
    assert exc.value.code == "validation_error"
