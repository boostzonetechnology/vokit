from __future__ import annotations

from shared_kernel.errors import DomainError

STT_TTS_CODES = frozenset({"deepgram", "elevenlabs", "cartesia"})
LLM_CODES = frozenset({"openai", "grok", "anthropic"})

VOICE_API_KEY_KEYS: dict[str, str] = {
    "deepgram": "voice.deepgram.api_key",
    "cartesia": "voice.cartesia.api_key",
    "elevenlabs": "voice.elevenlabs.api_key",
    "openai": "voice.openai.api_key",
    "grok": "voice.grok.api_key",
    "anthropic": "voice.anthropic.api_key",
}

VOICE_SECRET_KEYS = frozenset(VOICE_API_KEY_KEYS.values())

_KIND_CODES = {
    "telephony.stt_provider": STT_TTS_CODES,
    "telephony.tts_provider": STT_TTS_CODES,
    "telephony.llm_provider": LLM_CODES,
}


def is_voice_secret_key(key: str) -> bool:
    return key in VOICE_SECRET_KEYS


def api_key_setting_for(vendor: str) -> str | None:
    return VOICE_API_KEY_KEYS.get((vendor or "").strip().lower())


def assert_provider_code(key: str, raw: str) -> str:
    allowed = _KIND_CODES.get(key)
    if allowed is None:
        return raw
    value = (raw or "").strip().lower()
    if value == "":
        return ""
    if value not in allowed:
        raise DomainError("validation_error", f"{key} is invalid.")
    return value
