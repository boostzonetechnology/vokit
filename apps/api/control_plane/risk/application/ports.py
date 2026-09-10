from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.risk.domain.types import RiskStatus, VerificationStatus


@dataclass(frozen=True, slots=True)
class RiskCaseRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    status: RiskStatus
    last_invoice_id: uuid.UUID | None
    last_payment_id: uuid.UUID | None
    last_event_id: str
    note: str
    permanently_banned: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RiskEventRecord:
    processor: str
    event_id: str
    customer_id: uuid.UUID | None
    kind: str
    status: str


@dataclass(frozen=True, slots=True)
class VerificationRecord:
    id: uuid.UUID
    case_id: uuid.UUID
    status: VerificationStatus
    id_object_ref: str
    id_checksum: str
    card_object_ref: str
    card_checksum: str
    card_last4: str


class RiskCaseRepository(Protocol):
    def get(self, case_id: uuid.UUID) -> RiskCaseRecord | None: ...

    def get_for_customer(self, customer_id: uuid.UUID) -> RiskCaseRecord | None: ...

    def list(self, *, status: RiskStatus | None = None) -> list[RiskCaseRecord]: ...

    def upsert(self, record: RiskCaseRecord) -> None: ...


class RiskEventRepository(Protocol):
    def get(self, processor: str, event_id: str) -> RiskEventRecord | None: ...

    def create(self, record: RiskEventRecord) -> None: ...

    def list(self, *, kind: str | None = None) -> list[RiskEventRecord]: ...


class VerificationRepository(Protocol):
    def create(self, record: VerificationRecord) -> None: ...

    def latest_for_case(self, case_id: uuid.UUID) -> VerificationRecord | None: ...


class CustomerEmailLookup(Protocol):
    def emails_for_customer(self, customer_id: uuid.UUID) -> list[str]: ...
