from __future__ import annotations

import logging

from control_plane.platform_settings.application.service import PlatformSettingsControl
from control_plane.platform_settings.domain.voice_catalog import (
    LLM_CODES,
    STT_TTS_CODES,
    api_key_setting_for,
)
from providers.voice.models_catalog import list_provider_models
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.voice")


class ListProviderModels:
    """List vendor models using that vendor's stored Family B key (settings UI)."""

    def __init__(self, settings: PlatformSettingsControl) -> None:
        self._settings = settings

    def execute(self, *, vendor: str, capability: str) -> dict[str, object]:
        code = (vendor or "").strip().lower()
        kind = (capability or "").strip().lower()
        if kind == "llm":
            allowed = LLM_CODES
        elif kind in {"stt", "tts"}:
            allowed = STT_TTS_CODES
        else:
            raise DomainError("validation_error", "capability is invalid.")
        if code not in allowed:
            raise DomainError(
                "validation_error",
                f"vendor is invalid for capability={kind}.",
            )
        if api_key_setting_for(code) is None:
            raise DomainError(
                "voice_provider_not_configured",
                "Provider is not configured.",
                http_status=503,
            )
        api_key = self._settings.decrypted_vendor_key(code)
        if not api_key:
            raise DomainError(
                "secret_missing",
                "Required secret is not configured.",
                http_status=503,
            )
        try:
            payload = list_provider_models(code, kind, api_key)
        except DomainError:
            log_event(
                logger,
                "provider.models.listed",
                outcome="error",
                provider=code,
                capability=kind,
            )
            raise
        models = payload.get("models")
        log_event(
            logger,
            "provider.models.listed",
            outcome="success",
            provider=code,
            capability=kind,
            model_count=len(models) if isinstance(models, list) else 0,
        )
        return payload
