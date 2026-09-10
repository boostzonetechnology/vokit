from __future__ import annotations

import uuid
from dataclasses import dataclass

from control_plane.telephony.application.ports import (
    NumberProvider,
    PhoneNumberRecord,
    PhoneNumberRepository,
)
from control_plane.telephony.domain.policies import number_e164, parse_capabilities
from control_plane.telephony.domain.types import NumberStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.money import V1_CURRENCY, Money


@dataclass(frozen=True, slots=True)
class StockNumberCommand:
    e164: str
    country: str
    area: str = ""
    capabilities: object = None
    monthly_cost_minor: int = 0
    provider: str = "platform"
    provider_ref: str = ""


class StockNumber:
    def __init__(self, numbers: PhoneNumberRepository, clock: Clock) -> None:
        self._numbers = numbers
        self._clock = clock

    def execute(self, command: StockNumberCommand) -> PhoneNumberRecord:
        e164 = number_e164(command.e164)
        existing = self._numbers.get_by_e164(e164)
        if existing is not None:
            return existing
        if type(command.monthly_cost_minor) is not int or command.monthly_cost_minor < 0:
            raise DomainError("validation_error", "monthly_cost_minor must be >= 0.")
        now = self._clock.now()
        return self._numbers.save(
            PhoneNumberRecord(
                id=new_uuid7(),
                e164=e164,
                country=(command.country or "").strip().upper() or "US",
                area=(command.area or "").strip(),
                capabilities=parse_capabilities(command.capabilities),
                provider=(command.provider or "platform").strip() or "platform",
                provider_ref=(command.provider_ref or "").strip(),
                status=NumberStatus.AVAILABLE,
                monthly_cost=Money(command.monthly_cost_minor, V1_CURRENCY),
                created_at=now,
                updated_at=now,
            )
        )


@dataclass(frozen=True, slots=True)
class PurchaseNumberCommand:
    e164: str
    actor_id: uuid.UUID
    idempotency_key: str


class PurchaseNumber:
    def __init__(
        self,
        numbers: PhoneNumberRepository,
        provider: NumberProvider,
        clock: Clock,
    ) -> None:
        self._numbers = numbers
        self._provider = provider
        self._clock = clock

    def execute(self, command: PurchaseNumberCommand) -> PhoneNumberRecord:
        key = command.idempotency_key.strip()
        if not key:
            raise DomainError("validation_error", "Idempotency-Key is required.")
        e164 = number_e164(command.e164)
        existing = self._numbers.get_by_e164(e164)
        if existing is not None:
            return existing
        offer = self._provider.purchase(e164=e164, idempotency_key=key)
        now = self._clock.now()
        return self._numbers.save(
            PhoneNumberRecord(
                id=new_uuid7(),
                e164=offer.e164,
                country=offer.country,
                area=offer.area,
                capabilities=offer.capabilities,
                provider=offer.provider,
                provider_ref=offer.provider_ref,
                status=NumberStatus.AVAILABLE,
                monthly_cost=offer.monthly_cost,
                created_at=now,
                updated_at=now,
            )
        )
