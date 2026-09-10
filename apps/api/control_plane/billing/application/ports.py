from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.billing.domain.types import (
    InvoiceStatus,
    PlanStatus,
    ProcessorEventStatus,
)
from shared_kernel.money import Money


@dataclass(frozen=True, slots=True)
class PlanRecord:
    id: uuid.UUID
    name: str
    status: PlanStatus
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PlanVersionRecord:
    id: uuid.UUID
    plan_id: uuid.UUID
    version: int
    price: Money
    included_minutes: int
    allow_topups: bool
    topup_minutes: int
    topup_price: Money
    overage_enabled: bool
    overage_price_per_minute: Money
    grace_seconds: int
    used_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class InvoiceIndexRecord:
    invoice_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    status: InvoiceStatus
    total: Money
    created_at: datetime | None = None
    paid_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ProcessorEventRecord:
    processor: str
    event_id: str
    invoice_id: uuid.UUID | None
    status: ProcessorEventStatus


@dataclass(frozen=True, slots=True)
class BillingSettingsRecord:
    stripe_webhook_secret_ref: str
    braintree_webhook_secret_ref: str


@dataclass(frozen=True, slots=True)
class NormalizedPaymentEvent:
    processor: str
    event_id: str
    invoice_id: uuid.UUID
    amount: Money
    captured: bool
    chargeback: bool = False
    risk_flagged: bool = False


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    actor_id: uuid.UUID
    key: str
    kind: str
    resource_id: uuid.UUID


class PlanRepository(Protocol):
    def create(self, record: PlanRecord) -> None: ...

    def get(self, plan_id: uuid.UUID) -> PlanRecord | None: ...

    def list(self, *, status: PlanStatus | None = None) -> list[PlanRecord]: ...

    def update(self, record: PlanRecord) -> None: ...


class PlanVersionRepository(Protocol):
    def create(self, record: PlanVersionRecord) -> None: ...

    def get(self, version_id: uuid.UUID) -> PlanVersionRecord | None: ...

    def list_for_plan(self, plan_id: uuid.UUID) -> list[PlanVersionRecord]: ...

    def update(self, record: PlanVersionRecord) -> None: ...

    def next_version(self, plan_id: uuid.UUID) -> int: ...


class InvoiceIndexRepository(Protocol):
    def create(self, record: InvoiceIndexRecord) -> None: ...

    def get(self, invoice_id: uuid.UUID) -> InvoiceIndexRecord | None: ...

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
        status: InvoiceStatus | None = None,
    ) -> list[InvoiceIndexRecord]: ...

    def update(self, record: InvoiceIndexRecord) -> None: ...


class ProcessorEventRepository(Protocol):
    def get(self, processor: str, event_id: str) -> ProcessorEventRecord | None: ...

    def create(self, record: ProcessorEventRecord) -> None: ...


class BillingSettingsRepository(Protocol):
    def get(self) -> BillingSettingsRecord: ...


class BillingIdempotencyRepository(Protocol):
    def get(self, actor_id: uuid.UUID, key: str) -> IdempotencyRecord | None: ...

    def create(self, record: IdempotencyRecord) -> None: ...


class CommissionAccrual(Protocol):
    def on_captured_payment(
        self,
        *,
        payment: object,
        invoice: object,
        settled_at: datetime,
    ) -> object | None: ...


class PaymentProcessor(Protocol):
    slug: str

    def verify_and_normalize(
        self, *, raw_body: bytes, signature_header: str, secret_ref: str
    ) -> NormalizedPaymentEvent: ...
