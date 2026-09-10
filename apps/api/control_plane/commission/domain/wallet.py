"""Authoritative wallet buckets are projections of immutable ledger entries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from control_plane.commission.domain.types import (
    CommissionState,
    LedgerKind,
)
from shared_kernel.money import V1_CURRENCY, Money


@dataclass(frozen=True, slots=True)
class LedgerView:
    id: object
    kind: LedgerKind
    amount_minor: int
    currency: str
    commission_id: object | None
    payout_id: object | None
    earned_at: datetime | None
    available_at: datetime | None


@dataclass(frozen=True, slots=True)
class WalletBuckets:
    pending_minor: int
    on_hold_minor: int
    available_minor: int
    frozen_minor: int
    withdrawal_pending_minor: int
    lifetime_paid_minor: int
    currency: str = V1_CURRENCY

    def as_money(self) -> dict[str, int | str]:
        return {
            "pending_minor": self.pending_minor,
            "on_hold_minor": self.on_hold_minor,
            "available_minor": self.available_minor,
            "frozen_minor": self.frozen_minor,
            "withdrawal_pending_minor": self.withdrawal_pending_minor,
            "lifetime_paid_minor": self.lifetime_paid_minor,
            "currency": self.currency,
        }


def project_wallet(entries: tuple[LedgerView, ...], now: datetime) -> WalletBuckets:
    frozen = _wallet_frozen(entries)
    reversed_ids = {
        row.commission_id
        for row in entries
        if row.kind is LedgerKind.COMMISSION_REVERSAL and row.commission_id is not None
    }
    released_ids = {
        row.commission_id
        for row in entries
        if row.kind is LedgerKind.HOLD_RELEASED and row.commission_id is not None
    }
    on_hold = 0
    matured = 0
    for row in entries:
        if row.kind is not LedgerKind.COMMISSION_EARNED:
            continue
        if row.id in reversed_ids:
            continue
        hold_open = row.available_at is not None and now < row.available_at
        if hold_open and row.id not in released_ids:
            on_hold += row.amount_minor
        else:
            matured += row.amount_minor
    credits = sum(
        row.amount_minor for row in entries if row.kind is LedgerKind.MANUAL_CREDIT
    )
    debits = sum(
        row.amount_minor for row in entries if row.kind is LedgerKind.MANUAL_DEBIT
    )
    reserved = sum(
        row.amount_minor for row in entries if row.kind is LedgerKind.PAYOUT_RESERVED
    )
    released = sum(
        row.amount_minor for row in entries if row.kind is LedgerKind.PAYOUT_RELEASED
    )
    paid = sum(row.amount_minor for row in entries if row.kind is LedgerKind.PAYOUT_PAID)
    available = matured + credits - debits - reserved + released
    if frozen:
        return WalletBuckets(
            pending_minor=0,
            on_hold_minor=0,
            available_minor=0,
            frozen_minor=on_hold + available,
            withdrawal_pending_minor=reserved - released - paid,
            lifetime_paid_minor=paid,
        )
    return WalletBuckets(
        pending_minor=0,
        on_hold_minor=on_hold,
        available_minor=available,
        frozen_minor=0,
        withdrawal_pending_minor=reserved - released - paid,
        lifetime_paid_minor=paid,
    )


def commission_state(
    entry: LedgerView,
    entries: tuple[LedgerView, ...],
    now: datetime,
) -> CommissionState:
    if any(
        row.kind is LedgerKind.COMMISSION_REVERSAL and row.commission_id == entry.id
        for row in entries
    ):
        return CommissionState.REVERSED
    if _wallet_frozen(entries):
        return CommissionState.FROZEN
    released = any(
        row.kind is LedgerKind.HOLD_RELEASED and row.commission_id == entry.id
        for row in entries
    )
    if entry.available_at is not None and now < entry.available_at and not released:
        return CommissionState.ON_HOLD
    return CommissionState.AVAILABLE


def available_money(buckets: WalletBuckets) -> Money:
    return Money(buckets.available_minor, buckets.currency)


def _wallet_frozen(entries: tuple[LedgerView, ...]) -> bool:
    frozen = False
    for row in entries:
        if row.kind is LedgerKind.WALLET_FROZEN:
            frozen = True
        elif row.kind is LedgerKind.WALLET_UNFROZEN:
            frozen = False
    return frozen
