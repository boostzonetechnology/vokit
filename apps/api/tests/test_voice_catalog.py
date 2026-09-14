from __future__ import annotations

from providers.voice.catalog import list_tts_voices
from shared_kernel.errors import DomainError


def test_cartesia_voices_are_normalized(monkeypatch) -> None:
    def fake_get(url: str, headers: dict[str, str], *, timeout: float = 5.0):
        assert "cartesia.ai" in url
        assert headers["X-API-Key"] == "ck_test"
        return {"data": [{"id": "voice-a", "name": "Ava", "language": "en"}]}

    monkeypatch.setattr("providers.voice.catalog.vendor_get", fake_get)
    payload = list_tts_voices("cartesia", "ck_test")
    assert payload == {
        "provider": "cartesia",
        "voices": [{"id": "voice-a", "name": "Ava", "language": "en"}],
    }


def test_elevenlabs_and_deepgram_voices_are_normalized(monkeypatch) -> None:
    def fake_get(url: str, headers: dict[str, str], *, timeout: float = 5.0):
        if "elevenlabs" in url:
            return {
                "voices": [
                    {
                        "voice_id": "11-1",
                        "name": "Rachel",
                        "labels": {"language": "en"},
                    }
                ]
            }
        return {
            "tts": [
                {
                    "canonical_name": "aura-2-thalia-en",
                    "name": "Thalia",
                    "languages": ["en"],
                }
            ]
        }

    monkeypatch.setattr("providers.voice.catalog.vendor_get", fake_get)
    eleven = list_tts_voices("elevenlabs", "el_test")
    assert eleven["voices"][0]["id"] == "11-1"
    deepgram = list_tts_voices("deepgram", "dg_test")
    assert deepgram["voices"][0]["id"] == "aura-2-thalia-en"


def test_unknown_tts_provider_is_rejected() -> None:
    try:
        list_tts_voices("openai", "x")
    except DomainError as exc:
        assert exc.code == "voice_provider_not_configured"
        assert exc.http_status == 503
    else:
        raise AssertionError("expected DomainError")
