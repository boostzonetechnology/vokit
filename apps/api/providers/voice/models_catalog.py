"""Map vendor model-list APIs onto a normalized catalog (not hardcoded)."""

from __future__ import annotations

from providers.voice.http import vendor_get
from shared_kernel.errors import DomainError

CARTESIA_VERSION = "2024-06-10"
ANTHROPIC_VERSION = "2023-06-01"


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
        return _openai_style_models(body)
    if code == "grok":
        body = vendor_get(
            "https://api.x.ai/v1/models",
            {"Authorization": f"Bearer {api_key}"},
        )
        return _openai_style_models(body)
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


def _speech_models(code: str, kind: str, api_key: str) -> list[dict[str, str]]:
    if code == "deepgram":
        return _deepgram_models(api_key, kind)
    if code == "elevenlabs":
        return _elevenlabs_models(api_key)
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


def _elevenlabs_models(api_key: str) -> list[dict[str, str]]:
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
        mapped = _model(item.get("model_id") or item.get("id"), item.get("name"))
        if mapped is not None:
            models.append(mapped)
    return models


def _cartesia_models(api_key: str, kind: str) -> list[dict[str, str]]:
    # Cartesia exposes voices as the selectable catalog for TTS; STT has limited public list.
    if kind == "tts":
        body = vendor_get(
            "https://api.cartesia.ai/voices",
            {"X-API-Key": api_key, "Cartesia-Version": CARTESIA_VERSION},
        )
        rows = body.get("data") if isinstance(body, dict) else body
        if not isinstance(rows, list):
            rows = []
        models: list[dict[str, str]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            mapped = _model(item.get("id"), item.get("name"))
            if mapped is not None:
                models.append(mapped)
        return models
    # Prefer models endpoint when available; fall back empty rather than inventing IDs.
    try:
        body = vendor_get(
            "https://api.cartesia.ai/models",
            {"X-API-Key": api_key, "Cartesia-Version": CARTESIA_VERSION},
        )
    except DomainError:
        return []
    rows = body.get("data") if isinstance(body, dict) else body
    if not isinstance(rows, list):
        rows = []
    models = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        mapped = _model(item.get("id"), item.get("name") or item.get("id"))
        if mapped is not None:
            models.append(mapped)
    return models
