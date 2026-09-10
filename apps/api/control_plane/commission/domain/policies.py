from __future__ import annotations

from datetime import datetime, timedelta

from control_plane.billing.domain.types import LineKind
from control_plane.commission.domain.types import HOLD_DAYS, PayoutStatus
from shared_kernel.errors import DomainError
from shared_kernel.money import V1_CURRENCY, Money


def hold_available_at(earned_at: datetime, hold_days: int | None = None) -> datetime:
    days = HOLD_DAYS if hold_days is None else int(hold_days)
    if days < 0 or days > 365:
        raise DomainError("validation_error", "hold_days is invalid.")
    return earned_at + timedelta(days=days)


def eligible_base_from_lines(
    lines: tuple[tuple[LineKind | str, int, str, bool], ...],
) -> Money:
    """Captured cash excluding tax/promo/pass-through. Processor fees ignored (Q-012)."""
    acc = Money(0, V1_CURRENCY)
    for _kind, amount_minor, currency, commissionable in lines:
        if not commissionable:
            continue
        acc = acc + Money(amount_minor, currency)
    return acc


def commission_amount(base: Money, rate_bps: int) -> Money:
    if type(rate_bps) is not int or rate_bps < 0 or rate_bps > 10000:
        raise DomainError("validation_error", "commission_rate_bps is invalid.")
    return Money(base.minor_units * rate_bps // 10000, base.currency)


def assert_payout_amount(amount: Money, available: Money) -> None:
    if amount.minor_units < 1:
        raise DomainError("validation_error", "amount_minor must be a positive integer.")
    if amount.currency != available.currency:
        raise DomainError("currency_mismatch", "Payout currency does not match the wallet.")
    if amount.minor_units > available.minor_units:
        raise DomainError(
            "payout_insufficient",
            "Only available wallet balance can be withdrawn.",
            http_status=409,
        )


def assert_payout_transition(current: PayoutStatus, action: str) -> PayoutStatus:
    allowed = {
        "approve": {PayoutStatus.REQUESTED},
        "reject": {PayoutStatus.REQUESTED, PayoutStatus.APPROVED, PayoutStatus.FROZEN},
        "process": {PayoutStatus.APPROVED},
        "freeze": {
            PayoutStatus.REQUESTED,
            PayoutStatus.APPROVED,
            PayoutStatus.PROCESSING,
        },
        "mark_paid": {PayoutStatus.APPROVED, PayoutStatus.PROCESSING},
    }.get(action)
    if allowed is None:
        raise DomainError("validation_error", "Unknown payout action.")
    if current not in allowed:
        raise DomainError(
            "invalid_payout_status",
            "Payout transition is not allowed.",
            http_status=409,
        )
    return {
        "approve": PayoutStatus.APPROVED,
        "reject": PayoutStatus.REJECTED,
        "process": PayoutStatus.PROCESSING,
        "freeze": PayoutStatus.FROZEN,
        "mark_paid": PayoutStatus.PAID,
    }[action]


def payout_not_found() -> DomainError:
    return DomainError("not_found", "Resource not found.", http_status=404)
