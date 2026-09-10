from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.commission.domain.types import LedgerKind, PayoutStatus


@dataclass(frozen=True, slots=True)
class LedgerEntryRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID | None
    kind: LedgerKind
    amount_minor: int
    currency: str
    payment_id: uuid.UUID | None
    invoice_id: uuid.UUID | None
    commission_id: uuid.UUID | None
    payout_id: uuid.UUID | None
    eligible_base_minor: int | None
    rate_bps_snapshot: int | None
    earned_at: datetime | None
    available_at: datetime | None
    reason: str
    actor_id: uuid.UUID | None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PayoutRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    amount_minor: int
    currency: str
    status: PayoutStatus
    method_label: str
    transaction_ref: str
    receipt_number: str
    requested_by_id: uuid.UUID
    decided_by_id: uuid.UUID | None
    requested_at: datetime | None
    paid_at: datetime | None


@dataclass(frozen=True, slots=True)
class PayoutProofRecord:
    payout_id: uuid.UUID
    object_ref: str
    content_type: str
    checksum: str
    uploaded_by_id: uuid.UUID


class LedgerRepository(Protocol):
    def append(self, entry: LedgerEntryRecord) -> None: ...

    def list_for_tenant(self, tenant_id: uuid.UUID) -> list[LedgerEntryRecord]: ...

    def list_all(self) -> list[LedgerEntryRecord]: ...

    def get(self, entry_id: uuid.UUID) -> LedgerEntryRecord | None: ...

    def get_earned_by_payment(self, payment_id: uuid.UUID) -> LedgerEntryRecord | None: ...

    def has_hold_release(self, commission_id: uuid.UUID) -> bool: ...

    def lock_tenant(self, tenant_id: uuid.UUID) -> None: ...


class PayoutRepository(Protocol):
    def create(self, record: PayoutRecord) -> None: ...

    def get(self, payout_id: uuid.UUID) -> PayoutRecord | None: ...

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        status: PayoutStatus | None = None,
    ) -> list[PayoutRecord]: ...

    def update_status(self, record: PayoutRecord) -> None: ...


class PayoutProofRepository(Protocol):
    def create(self, record: PayoutProofRecord) -> None: ...

    def get(self, payout_id: uuid.UUID) -> PayoutProofRecord | None: ...


class CommissionIdempotencyRepository(Protocol):
    def get(self, actor_id: uuid.UUID, key: str) -> uuid.UUID | None: ...

    def create(self, actor_id: uuid.UUID, key: str, resource_id: uuid.UUID) -> None: ...
