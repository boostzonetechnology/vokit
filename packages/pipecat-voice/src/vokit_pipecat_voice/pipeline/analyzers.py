"""Load Silero VAD and Smart Turn without blocking the media WebSocket loop."""
from __future__ import annotations

from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

_VAD_PARAMS = VADParams(
    confidence=0.5,
    start_secs=0.2,
    stop_secs=0.4,
    min_volume=0.3,
)


def build_vad_analyzer(sample_rate: int) -> SileroVADAnalyzer:
    return SileroVADAnalyzer(sample_rate=sample_rate, params=_VAD_PARAMS)


def build_vad_and_turn_analyzers(
    sample_rate: int,
) -> tuple[SileroVADAnalyzer, LocalSmartTurnAnalyzerV3]:
    """Construct per-call analyzers. Call from ``asyncio.to_thread``."""
    return build_vad_analyzer(sample_rate), LocalSmartTurnAnalyzerV3()


def preload_voice_models(sample_rate: int = 8000) -> None:
    """Warm ONNX runtimes at process start. Instances are not reused across calls."""
    build_vad_and_turn_analyzers(sample_rate)
