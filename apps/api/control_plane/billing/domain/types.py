from __future__ import annotations

from enum import StrEnum


class PlanStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


class InvoiceStatus(StrEnum):
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    FAILED = "failed"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    CAPTURED = "captured"
    FAILED = "failed"


class LineKind(StrEnum):
    SUBSCRIPTION = "subscription"
    TOPUP = "topup"
    OVERAGE = "overage"
    TAX = "tax"
    PROMO = "promo"
    PASSTHROUGH = "passthrough"
    NUMBER = "number"


class LotKind(StrEnum):
    INCLUDED = "included"
    TOPUP = "topup"
    ADJUSTMENT = "adjustment"
    OVERAGE = "overage"


class ProcessorSlug(StrEnum):
    STRIPE = "stripe"
    BRAINTREE = "braintree"


class ProcessorEventStatus(StrEnum):
    RECEIVED = "received"
    PROCESSED = "processed"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


DRAIN_ORDER: tuple[LotKind, ...] = (
    LotKind.INCLUDED,
    LotKind.TOPUP,
    LotKind.ADJUSTMENT,
    LotKind.OVERAGE,
)

COMMISSIONABLE_BY_DEFAULT: frozenset[LineKind] = frozenset(
    {LineKind.SUBSCRIPTION, LineKind.TOPUP, LineKind.OVERAGE}
)
