"""Turn-strategy wiring shared by the inbound pipeline builder."""
from __future__ import annotations

import struct
from typing import Any

from pipecat.processors.aggregators.llm_response_universal import LLMUserAggregatorParams
from pipecat.turns.user_stop import TurnAnalyzerUserTurnStopStrategy
from pipecat.turns.user_turn_strategies import (
    ExternalUserTurnStrategies,
    UserTurnStrategies,
    default_user_turn_start_strategies,
)


def pcm16_rms(pcm: bytes) -> float:
    """RMS of 16-bit PCM samples (ITU μ-law silence decodes to 0)."""
    if len(pcm) < 2:
        return 0.0
    n = len(pcm) // 2
    samples = struct.unpack(f"<{n}h", pcm[: n * 2])
    acc = sum(sample * sample for sample in samples)
    return (acc / n) ** 0.5


def user_aggregator_params(stt: Any, vad_analyzer: Any, turn_analyzer: Any | None) -> LLMUserAggregatorParams:
    """Cartesia ink-2 must keep server-driven turns; Deepgram/ElevenLabs use VAD+Smart Turn.

    Passing any ``user_turn_strategies`` makes the aggregator ignore
    CartesiaTurnsSTTService's ExternalUserTurnStrategies recommendation.
    https://docs.pipecat.ai/api-reference/server/services/stt/cartesia
    """
    if stt.__class__.__name__ == "CartesiaTurnsSTTService":
        return LLMUserAggregatorParams(
            vad_analyzer=vad_analyzer,
            user_turn_strategies=ExternalUserTurnStrategies(),
        )
    return LLMUserAggregatorParams(
        vad_analyzer=vad_analyzer,
        user_turn_strategies=UserTurnStrategies(
            start=default_user_turn_start_strategies(),
            stop=[TurnAnalyzerUserTurnStopStrategy(turn_analyzer=turn_analyzer)],
        ),
    )
