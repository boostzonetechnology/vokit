from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from control_plane.billing.domain.types import (
    InvoiceStatus,
    LineKind,
    LotKind,
    PaymentStatus,
    SubscriptionStatus,
)


@dataclass(frozen=True, slots=True)
class SubscriptionRecord:
    subscription_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    plan_version_id: uuid.UUID
    status: SubscriptionStatus
    cycle: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class InvoiceLineRecord:
    line_id: uuid.UUID
    kind: LineKind
    description: str
    amount_minor: int
    currency: str
    minutes: int
    commissionable: bool


@dataclass(frozen=True, slots=True)
class InvoiceRecord:
    invoice_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    subscription_id: uuid.UUID | None
    status: InvoiceStatus
    currency: str
    total_minor: int
    lines: tuple[InvoiceLineRecord, ...]
    created_at: datetime | None = None
    updated_at: datetime | None = None
    paid_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PaymentRecord:
    payment_id: uuid.UUID
    invoice_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    processor: str
    processor_event_id: str
    amount_minor: int
    currency: str
    status: PaymentStatus
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MinuteLotRecord:
    lot_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    invoice_id: uuid.UUID
    kind: LotKind
    granted_minutes: int
    remaining_minutes: int
    created_at: datetime | None = None
