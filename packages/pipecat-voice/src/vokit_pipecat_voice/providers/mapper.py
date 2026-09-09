"""Map Django bootstrap provider snapshots onto Pipecat service constructors.

Django App Settings remain the selection UI and credential store.
This module only constructs runtime Pipecat services for the current call.
"""
from __future__ import annotations

from typing import Any

from pipecat.frames.frames import ErrorFrame
from pipecat.processors.frame_processor import FrameProcessor


class UnsupportedProviderError(Exception):
    """Django selected a vendor that this Pipecat process cannot construct."""


def _settings_or_kwargs(cls: type, *, api_key: str, settings_kwargs: dict[str, Any], **init_kwargs):
    settings_cls = getattr(cls, "Settings", None)
    if settings_cls is not None:
        filtered = {k: v for k, v in settings_kwargs.items() if v not in (None, "")}
        try:
            return cls(api_key=api_key, settings=settings_cls(**filtered), **init_kwargs)
        except TypeError:
            pass
    merged = {k: v for k, v in settings_kwargs.items() if v not in (None, "")}
    merged.update(init_kwargs)
    return cls(api_key=api_key, **merged)


def build_stt(spec: dict[str, Any]) -> FrameProcessor:
    code = (spec.get("provider_code") or "").strip().lower()
    api_key = spec.get("api_key") or ""
    model = spec.get("model") or ""
    language = spec.get("language") or "en"
    if code == "deepgram":
        from pipecat.services.deepgram.stt import DeepgramSTTService

        return _settings_or_kwargs(
            DeepgramSTTService,
            api_key=api_key,
            settings_kwargs={
                "model": model or "nova-3",
                "language": language,
                "interim_results": True,
                # utterance_end_ms MUST be >= 1000 or Deepgram rejects the
                # Listen WebSocket with HTTP 400 (handshake fails → call hangup).
                # https://developers.deepgram.com/docs/utterance-end
                "endpointing": 300,
                "utterance_end_ms": 1000,
                "punctuate": True,
                "smart_format": True,
            },
            encoding="linear16",
        )
    if code == "elevenlabs":
        from pipecat.services.elevenlabs.stt import ElevenLabsSTTService

        return _settings_or_kwargs(
            ElevenLabsSTTService,
            api_key=api_key,
            settings_kwargs={"model": model or "scribe_v2", "language": language},
        )
    if code == "cartesia":
        # ink-2 is the v2 turns API. CartesiaSTTService is v1 (ink-whisper) on
        # /stt/websocket and will connect but never emit turn transcripts.
        # https://docs.pipecat.ai/api-reference/server/services/stt/cartesia
        resolved = (model or "ink-2").strip().lower()
        if resolved.startswith("ink-2"):
            from pipecat.services.cartesia.turns.stt import CartesiaTurnsSTTService

            return _settings_or_kwargs(
                CartesiaTurnsSTTService,
                api_key=api_key,
                settings_kwargs={"model": resolved},
            )
        from pipecat.services.cartesia.stt import CartesiaSTTService

        return _settings_or_kwargs(
            CartesiaSTTService,
            api_key=api_key,
            settings_kwargs={"model": resolved or "ink-whisper", "language": language},
            encoding="pcm_s16le",
        )
    raise UnsupportedProviderError(f"Unsupported STT provider_code={code}")


def build_tts(spec: dict[str, Any]) -> FrameProcessor:
    """Build TTS. Prefer sentence aggregation for natural telephony speech.

    Cartesia TOKEN + max_buffer_delay_ms=0 synthesizes each LLM token as its
    own utterance (word… word… word). Official low-latency Cartesia path is
    SENTENCE aggregation with max_buffer_delay_ms=0 so the client waits for a
    sentence, then the server generates immediately (no 3000ms managed buffer).
    https://docs.cartesia.ai/use-the-api/tts-websocket/buffering
    https://docs.pipecat.ai/api-reference/server/services/tts/cartesia
    """
    from pipecat.services.tts_service import TextAggregationMode

    code = (spec.get("provider_code") or "").strip().lower()
    api_key = spec.get("api_key") or ""
    model = spec.get("model") or ""
    voice_id = spec.get("voice_id") or ""
    language = spec.get("language") or "en"
    if code == "deepgram":
        from pipecat.services.deepgram.tts import DeepgramTTSService

        voice = voice_id or model or "aura-2-thalia-en"
        return _settings_or_kwargs(
            DeepgramTTSService,
            api_key=api_key,
            settings_kwargs={"voice": voice, "model": voice},
            encoding="linear16",
            text_aggregation_mode=TextAggregationMode.SENTENCE,
        )
    if code == "elevenlabs":
        # SENTENCE enables ElevenLabs auto_mode (lower latency on full phrases).
        from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

        return _settings_or_kwargs(
            ElevenLabsTTSService,
            api_key=api_key,
            settings_kwargs={
                "voice": voice_id,
                "model": model or "eleven_multilingual_v2",
                "language": language,
            },
            text_aggregation_mode=TextAggregationMode.SENTENCE,
        )
    if code == "cartesia":
        # Slightly above default 1.0 so telephony doesn't feel drawn-out vs
        # Cartesia's web demo. Valid range [0.6, 1.5].
        # https://docs.pipecat.ai/api-reference/server/services/tts/cartesia
        from pipecat.services.cartesia.tts import CartesiaTTSService, GenerationConfig

        return _settings_or_kwargs(
            CartesiaTTSService,
            api_key=api_key,
            settings_kwargs={
                "voice": voice_id,
                "model": model or "sonic-3.5",
                "language": language,
                "generation_config": GenerationConfig(speed=1.35),
            },
            text_aggregation_mode=TextAggregationMode.SENTENCE,
            max_buffer_delay_ms=0,
        )
    raise UnsupportedProviderError(f"Unsupported TTS provider_code={code}")


def build_llm(spec: dict[str, Any]) -> FrameProcessor:
    code = (spec.get("provider_code") or "").strip().lower()
    api_key = spec.get("api_key") or ""
    model = spec.get("model") or ""
    if code == "openai":
        from pipecat.services.openai.llm import OpenAILLMService

        return _settings_or_kwargs(
            OpenAILLMService,
            api_key=api_key,
            settings_kwargs={"model": model or "gpt-4o-mini"},
        )
    if code == "grok":
        from pipecat.services.xai.llm import GrokLLMService

        return _settings_or_kwargs(
            GrokLLMService,
            api_key=api_key,
            settings_kwargs={"model": model or "grok-3-latest"},
        )
    if code == "google":
        try:
            from pipecat.services.google.llm import GoogleLLMService as LlmCls
        except ImportError:
            from pipecat.services.google.llm import GeminiLLMService as LlmCls

        return _settings_or_kwargs(
            LlmCls,
            api_key=api_key,
            settings_kwargs={"model": model or "gemini-2.0-flash"},
        )
    if code == "anthropic":
        from pipecat.services.anthropic.llm import AnthropicLLMService

        return _settings_or_kwargs(
            AnthropicLLMService,
            api_key=api_key,
            settings_kwargs={"model": model or "claude-sonnet-4-20250514"},
        )
    raise UnsupportedProviderError(f"Unsupported LLM provider_code={code}")


def build_pipeline_services(providers: dict[str, Any]) -> tuple[Any, Any, Any]:
    stt_spec = providers.get("stt") or {}
    tts_spec = providers.get("tts") or {}
    llm_spec = providers.get("llm") or {}
    try:
        return build_stt(stt_spec), build_tts(tts_spec), build_llm(llm_spec)
    except ImportError as exc:
        raise UnsupportedProviderError(str(exc)) from exc


class ErrorBridge(FrameProcessor):
    """Forward pipeline ErrorFrames to a callback (provider hard-fail)."""

    def __init__(self, on_error) -> None:
        super().__init__()
        self._on_error = on_error

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        if isinstance(frame, ErrorFrame):
            await self._on_error(frame)
        await self.push_frame(frame, direction)
