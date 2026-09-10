from __future__ import annotations

import uuid
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.telephony.domain.types import NumberStatus, ReservationStatus
from shared_kernel.money import Money


@dataclass(frozen=True, slots=True)
class PhoneNumberRecord:
    id: uuid.UUID
    e164: str
    country: str
    area: str
    capabilities: tuple[str, ...]
    provider: str
    provider_ref: str
    status: NumberStatus
    monthly_cost: Money
    assigned_tenant_id: uuid.UUID | None = None
    assigned_customer_id: uuid.UUID | None = None
    assigned_agent_id: uuid.UUID | None = None
    reservation_id: uuid.UUID | None = None
    reserved_until: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ReservationRecord:
    id: uuid.UUID
    number_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    agent_id: uuid.UUID
    status: ReservationStatus
    expires_at: datetime
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ProviderNumberOffer:
    e164: str
    country: str
    area: str
    capabilities: tuple[str, ...]
    monthly_cost: Money
    provider: str
    provider_ref: str


class PhoneNumberRepository(Protocol):
    def transaction(self) -> AbstractContextManager[None]: ...
    def get(self, number_id: uuid.UUID) -> PhoneNumberRecord | None: ...
    def get_by_e164(self, e164: str) -> PhoneNumberRecord | None: ...
    def list(
        self,
        *,
        status: NumberStatus | None = None,
        country: str = "",
        area: str = "",
        capability: str = "",
        tenant_id: uuid.UUID | None = None,
    ) -> list[PhoneNumberRecord]: ...
    def save(self, record: PhoneNumberRecord) -> PhoneNumberRecord: ...
    def lock(self, number_id: uuid.UUID) -> PhoneNumberRecord | None: ...


class ReservationRepository(Protocol):
    def get(self, reservation_id: uuid.UUID) -> ReservationRecord | None: ...
    def active_for_number(self, number_id: uuid.UUID) -> ReservationRecord | None: ...
    def save(self, record: ReservationRecord) -> ReservationRecord: ...
    def list_expired(self, now: datetime) -> list[ReservationRecord]: ...


class NumberProvider(Protocol):
    def search(
        self, *, country: str = "", area: str = "", capability: str = ""
    ) -> list[ProviderNumberOffer]: ...

    def purchase(
        self, *, e164: str, idempotency_key: str
    ) -> ProviderNumberOffer: ...

    def release(self, *, provider_ref: str) -> None: ...

    def owned_refs(self) -> set[str]: ...
