from __future__ import annotations

import re
from dataclasses import dataclass

from shared_kernel.errors import DomainError
from shared_kernel.phone import normalize_e164


@dataclass(frozen=True, slots=True)
class ContinueDecision:
    continue_call: bool
    reason: str
    remaining_minutes: int
    in_grace: bool
    overage: bool


def normalize_did(raw: str) -> str:
    compact = re.sub(r"[\s().-]", "", (raw or "").strip())
    if compact.startswith("00"):
        compact = "+" + compact[2:]
    if compact.isdigit():
        compact = "+" + compact
    return normalize_e164(compact)


def billable_minutes(elapsed_seconds: int) -> int:
    if type(elapsed_seconds) is not int or elapsed_seconds < 0:
        raise DomainError("validation_error", "elapsed_seconds must be a non-negative integer.")
    if elapsed_seconds == 0:
        return 0
    return (elapsed_seconds + 59) // 60


def admit_usage(*, remaining_minutes: int, overage_enabled: bool, grace_seconds: int) -> str | None:
    if remaining_minutes > 0:
        return None
    if overage_enabled:
        return None
    if grace_seconds > 0:
        return None
    return "insufficient_minutes"


def decide_continue(
    *,
    remaining_minutes: int,
    elapsed_seconds: int,
    overage_enabled: bool,
    grace_seconds: int,
) -> ContinueDecision:
    used = billable_minutes(elapsed_seconds)
    leftover = max(0, remaining_minutes)
    if used <= leftover:
        return ContinueDecision(True, "ok", leftover - used, False, False)
    deficit_seconds = max(0, elapsed_seconds - leftover * 60)
    if overage_enabled:
        return ContinueDecision(True, "overage", 0, False, True)
    if grace_seconds > 0 and deficit_seconds <= grace_seconds:
        return ContinueDecision(True, "grace", 0, True, False)
    return ContinueDecision(False, "minutes_exhausted", 0, False, False)
