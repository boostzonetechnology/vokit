from __future__ import annotations

from datetime import datetime

from shared_kernel.errors import DomainError


def effective_commission_rate_bps(
    *,
    rate_bps: int,
    previous_rate_bps: int,
    rate_effective_at: datetime | None,
    at: datetime,
) -> int:
    if rate_effective_at is None or at >= rate_effective_at:
        return rate_bps
    return previous_rate_bps


def assert_commission_reason(reason: str) -> None:
    if not reason.strip():
        raise DomainError("validation_error", "reason is required.")
