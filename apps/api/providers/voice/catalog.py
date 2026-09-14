"""Map vendor TTS voice-list APIs onto the Vokit catalog contract."""

from __future__ import annotations

from providers.voice.http import vendor_get
from shared_kernel.errors import DomainError

CARTESIA_VERSION = "2024-06-10"


def list_tts_voices(provider: str, api_key: str) -> dict[str, object]:
    code = (provider or "").strip().lower()
    if code == "cartesia":
        voices = _cartesia(api_key)
    elif code == "elevenlabs":
        voices = _elevenlabs(api_key)
    elif code == "deepgram":
        voices = _deepgram(api_key)
    else:
        raise DomainError(
            "voice_provider_not_configured",
            "TTS provider is not configured.",
            http_status=503,
        )
    return {"provider": code, "voices": voices}


def _voice(voice_id: object, name: object, language: object) -> dict[str, str] | None:
    cleaned_id = str(voice_id or "").strip()
    if not cleaned_id:
        return None
    return {
        "id": cleaned_id,
        "name": str(name or cleaned_id).strip() or cleaned_id,
        "language": str(language or "").strip(),
    }


def _cartesia(api_key: str) -> list[dict[str, str]]:
    body = vendor_get(
        "https://api.cartesia.ai/voices",
        {"X-API-Key": api_key, "Cartesia-Version": CARTESIA_VERSION},
    )
    rows = body.get("data") if isinstance(body, dict) else body
    if not isinstance(rows, list):
        rows = []
    voices: list[dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        mapped = _voice(item.get("id"), item.get("name"), item.get("language"))
        if mapped is not None:
            voices.append(mapped)
    return voices


def _elevenlabs(api_key: str) -> list[dict[str, str]]:
    body = vendor_get(
        "https://api.elevenlabs.io/v1/voices",
        {"xi-api-key": api_key},
    )
    rows = body.get("voices") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        rows = []
    voices: list[dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        labels = item.get("labels") if isinstance(item.get("labels"), dict) else {}
        language = labels.get("language") or item.get("language")
        mapped = _voice(item.get("voice_id") or item.get("id"), item.get("name"), language)
        if mapped is not None:
            voices.append(mapped)
    return voices


def _deepgram(api_key: str) -> list[dict[str, str]]:
    body = vendor_get(
        "https://api.deepgram.com/v1/models",
        {"Authorization": f"Token {api_key}"},
    )
    rows = []
    if isinstance(body, dict):
        tts = body.get("tts")
        if isinstance(tts, list):
            rows = tts
    voices: list[dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        voice_id = item.get("canonical_name") or item.get("name") or item.get("id")
        languages = item.get("languages")
        language = ""
        if isinstance(languages, list) and languages:
            language = str(languages[0] or "")
        mapped = _voice(voice_id, item.get("name") or voice_id, language)
        if mapped is not None:
            voices.append(mapped)
    return voices
