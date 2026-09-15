"""Map vendor model catalogs onto a normalized contract (not agent voice_id lists)."""

from __future__ import annotations

from providers.voice.http import vendor_get
from shared_kernel.errors import DomainError

CARTESIA_VERSION = "2024-06-10"
ANTHROPIC_VERSION = "2023-06-01"

# Cartesia has no public list-models HTTP API. These IDs come from Cartesia docs/OpenAPI
# (TTSModelID + Ink STT). Voices must never be treated as telephony.*_model values.
CARTESIA_TTS_MODELS: tuple[tuple[str, str], ...] = (
    ("sonic-3.6", "Sonic 3.6"),
    ("sonic-3.5", "Sonic 3.5"),
    ("sonic-3", "Sonic 3"),
    ("sonic-2", "Sonic 2"),
    ("sonic-turbo", "Sonic Turbo"),
    ("sonic-preview", "Sonic Preview"),
    ("sonic-latest", "Sonic Latest"),
    ("sonic", "Sonic"),
)
CARTESIA_STT_MODELS: tuple[tuple[str, str], ...] = (
    ("ink-2", "Ink 2"),
    ("ink-whisper", "Ink Whisper"),
)


def list_provider_models(vendor: str, capability: str, api_key: str) -> dict[str, object]:
    code = (vendor or "").strip().lower()
    kind = (capability or "").strip().lower()
    if not api_key.strip():
        raise DomainError(
            "secret_missing",
            "Required secret is not configured.",
            http_status=503,
        )
    if kind == "llm":
        models = _llm_models(code, api_key)
    elif kind in {"stt", "tts"}:
        models = _speech_models(code, kind, api_key)
    else:
        raise DomainError("validation_error", "capability is invalid.")
    return {"provider": code, "capability": kind, "models": models}


def _model(model_id: object, name: object | None = None) -> dict[str, str] | None:
    cleaned = str(model_id or "").strip()
    if not cleaned:
        return None
    return {"id": cleaned, "name": str(name or cleaned).strip() or cleaned}


def _llm_models(code: str, api_key: str) -> list[dict[str, str]]:
    if code == "openai":
        body = vendor_get(
            "https://api.openai.com/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        )
        return _filter_openai_chat_models(_openai_style_models(body))
    if code == "grok":
        body = vendor_get(
            "https://api.x.ai/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        )
        return _filter_grok_chat_models(_openai_style_models(body))
    if code == "anthropic":
        body = vendor_get(
            "https://api.anthropic.com/v1/models",
            {
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
            },
        )
        rows = body.get("data") if isinstance(body, dict) else None
        if not isinstance(rows, list):
            rows = []
        models: list[dict[str, str]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            mapped = _model(item.get("id"), item.get("display_name") or item.get("id"))
            if mapped is not None:
                models.append(mapped)
        return models
    raise DomainError(
        "voice_provider_not_configured",
        "LLM provider is not configured.",
        http_status=503,
    )


def _openai_style_models(body: object) -> list[dict[str, str]]:
    rows = body.get("data") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        rows = []
    models: list[dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        mapped = _model(item.get("id"), item.get("id"))
        if mapped is not None:
            models.append(mapped)
    models.sort(key=lambda row: row["id"])
    return models


def _filter_openai_chat_models(models: list[dict[str, str]]) -> list[dict[str, str]]:
    kept: list[dict[str, str]] = []
    for row in models:
        model_id = row["id"].lower()
        if model_id.startswith(("gpt-", "o1", "o3", "o4", "chatgpt-")):
            kept.append(row)
    return kept or models


def _filter_grok_chat_models(models: list[dict[str, str]]) -> list[dict[str, str]]:
    kept: list[dict[str, str]] = []
    for row in models:
        model_id = row["id"].lower()
        if not model_id.startswith("grok"):
            continue
        if "image" in model_id or "vision" in model_id:
            continue
        kept.append(row)
    return kept


def _speech_models(code: str, kind: str, api_key: str) -> list[dict[str, str]]:
    if code == "deepgram":
        return _deepgram_models(api_key, kind)
    if code == "elevenlabs":
        return _elevenlabs_models(api_key, kind)
    if code == "cartesia":
        return _cartesia_models(api_key, kind)
    raise DomainError(
        "voice_provider_not_configured",
        "Speech provider is not configured.",
        http_status=503,
    )


def _deepgram_models(api_key: str, kind: str) -> list[dict[str, str]]:
    body = vendor_get(
        "https://api.deepgram.com/v1/models",
        {"Authorization": f"Token {api_key}"},
    )
    rows = []
    if isinstance(body, dict):
        section = body.get("tts" if kind == "tts" else "stt")
        if isinstance(section, list):
            rows = section
    models: list[dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        model_id = item.get("canonical_name") or item.get("name") or item.get("id")
        mapped = _model(model_id, item.get("name") or model_id)
        if mapped is not None:
            models.append(mapped)
    return models


def _elevenlabs_models(api_key: str, kind: str) -> list[dict[str, str]]:
    body = vendor_get(
        "https://api.elevenlabs.io/v1/models",
        {"xi-api-key": api_key},
    )
    rows = body if isinstance(body, list) else []
    if isinstance(body, dict):
        maybe = body.get("models")
        if isinstance(maybe, list):
            rows = maybe
    models: list[dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        if not _elevenlabs_matches_capability(item, kind):
            continue
        mapped = _model(item.get("model_id") or item.get("id"), item.get("name"))
        if mapped is not None:
            models.append(mapped)
    return models


def _elevenlabs_matches_capability(item: dict[str, object], kind: str) -> bool:
    model_id = str(item.get("model_id") or item.get("id") or "").lower()
    if kind == "tts":
        flag = item.get("can_do_text_to_speech")
        if isinstance(flag, bool):
            return flag
        return "scribe" not in model_id
    # STT / Scribe
    flag = item.get("can_do_speech_to_text")
    if isinstance(flag, bool):
        return flag
    return "scribe" in model_id


def _cartesia_models(api_key: str, kind: str) -> list[dict[str, str]]:
    # Probe credentials against a real Cartesia endpoint (voices), then return
    # documented model IDs — never the voice catalog (those are agent voice_id).
    vendor_get(
        "https://api.cartesia.ai/voices?limit=1",
        {"X-API-Key": api_key, "Cartesia-Version": CARTESIA_VERSION},
    )
    source = CARTESIA_TTS_MODELS if kind == "tts" else CARTESIA_STT_MODELS
    models: list[dict[str, str]] = []
    for model_id, name in source:
        mapped = _model(model_id, name)
        if mapped is not None:
            models.append(mapped)
    return models
