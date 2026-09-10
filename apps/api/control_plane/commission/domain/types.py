from __future__ import annotations

from enum import StrEnum

HOLD_DAYS = 15


class LedgerKind(StrEnum):
    COMMISSION_EARNED = "commission_earned"
    HOLD_RELEASED = "hold_released"
    COMMISSION_REVERSAL = "commission_reversal"
    MANUAL_CREDIT = "manual_credit"
    MANUAL_DEBIT = "manual_debit"
    PAYOUT_RESERVED = "payout_reserved"
    PAYOUT_RELEASED = "payout_released"
    PAYOUT_PAID = "payout_paid"
    WALLET_FROZEN = "wallet_frozen"
    WALLET_UNFROZEN = "wallet_unfrozen"


class CommissionState(StrEnum):
    ON_HOLD = "on_hold"
    AVAILABLE = "available"
    REVERSED = "reversed"
    FROZEN = "frozen"


class PayoutStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    PROCESSING = "processing"
    PAID = "paid"
    REJECTED = "rejected"
    FROZEN = "frozen"
