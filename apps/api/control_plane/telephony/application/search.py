from __future__ import annotations

import uuid
from dataclasses import dataclass

from control_plane.telephony.application.expiry import expire_stale_reservations
from control_plane.telephony.application.ports import (
    NumberProvider,
    PhoneNumberRecord,
    PhoneNumberRepository,
    ProviderNumberOffer,
    ReservationRepository,
)
from control_plane.telephony.domain.types import NumberStatus
from control_plane.tenancy.application.ports import Clock


@dataclass(frozen=True, slots=True)
class NumberSearchResult:
    inventory: list[PhoneNumberRecord]
    offers: list[ProviderNumberOffer]


class SearchNumbers:
    def __init__(
        self,
        numbers: PhoneNumberRepository,
        reservations: ReservationRepository,
        provider: NumberProvider,
        clock: Clock,
    ) -> None:
        self._numbers = numbers
        self._reservations = reservations
        self._provider = provider
        self._clock = clock

    def execute(
        self,
        *,
        country: str = "",
        area: str = "",
        capability: str = "",
        tenant_id: uuid.UUID | None = None,
        include_provider: bool = False,
    ) -> NumberSearchResult:
        expire_stale_reservations(self._numbers, self._reservations, self._clock.now())
        available = self._numbers.list(
            status=NumberStatus.AVAILABLE,
            country=country,
            area=area,
            capability=capability,
        )
        reserved_own: list[PhoneNumberRecord] = []
        if tenant_id is not None:
            for row in self._numbers.list(
                status=NumberStatus.RESERVED,
                country=country,
                area=area,
                capability=capability,
            ):
                held = self._reservations.active_for_number(row.id)
                if held is not None and held.tenant_id == tenant_id:
                    reserved_own.append(row)
        offers: list[ProviderNumberOffer] = []
        if include_provider:
            known = {row.e164 for row in self._numbers.list()}
            offers = [
                offer
                for offer in self._provider.search(
                    country=country, area=area, capability=capability
                )
                if offer.e164 not in known
            ]
        return NumberSearchResult(inventory=available + reserved_own, offers=offers)
