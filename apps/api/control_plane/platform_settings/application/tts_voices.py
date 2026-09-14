from __future__ import annotations

import logging

from control_plane.platform_settings.application.service import PlatformSettingsControl
from control_plane.platform_settings.domain.voice_catalog import STT_TTS_CODES
from providers.voice.catalog import list_tts_voices
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.voice")


class ListTtsVoices:
    def __init__(self, settings: PlatformSettingsControl) -> None:
        self._settings = settings

    def execute(self) -> dict[str, object]:
        provider = str(self._settings.stored_value("telephony.tts_provider") or "").strip().lower()
        if provider not in STT_TTS_CODES:
            raise DomainError(
                "voice_provider_not_configured",
                "TTS provider is not configured.",
                http_status=503,
            )
        api_key = self._settings.decrypted_vendor_key(provider)
        if not api_key:
            raise DomainError(
                "secret_missing",
                "Required secret is not configured.",
                http_status=503,
            )
        try:
            payload = list_tts_voices(provider, api_key)
        except DomainError:
            log_event(
                logger,
                "tts.voices.listed",
                outcome="error",
                provider=provider,
            )
            raise
        voices = payload.get("voices")
        log_event(
            logger,
            "tts.voices.listed",
            outcome="success",
            provider=provider,
            voice_count=len(voices) if isinstance(voices, list) else 0,
        )
        return payload
