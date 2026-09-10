from __future__ import annotations

import logging
from dataclasses import dataclass

from control_plane.telephony.application.expiry import expire_stale_reservations
from control_plane.telephony.application.ports import (
    NumberProvider,
    PhoneNumberRepository,
    ReservationRepository,
)
from control_plane.telephony.domain.types import NumberStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.telephony")


@dataclass(frozen=True, slots=True)
class ReconcileResult:
    expired_reservations: int
    provider_orphans: tuple[str, ...]
    local_orphans: tuple[str, ...]


class ReconcileNumbers:
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

    def execute(self) -> ReconcileResult:
        expired = expire_stale_reservations(
            self._numbers, self._reservations, self._clock.now()
        )
        owned = self._provider.owned_refs()
        provider_orphans: list[str] = []
        local_orphans: list[str] = []
        for row in self._numbers.list(status=NumberStatus.ASSIGNED):
            if row.provider_ref and row.provider_ref not in owned:
                provider_orphans.append(row.e164)
        for ref in owned:
            match = next(
                (row for row in self._numbers.list() if row.provider_ref == ref),
                None,
            )
            if match is None:
                local_orphans.append(ref)
        log_event(
            logger,
            "telephony.number.reconciled",
            outcome="success",
            expired_reservations=expired,
            provider_orphan_count=len(provider_orphans),
            local_orphan_count=len(local_orphans),
        )
        return ReconcileResult(
            expired_reservations=expired,
            provider_orphans=tuple(provider_orphans),
            local_orphans=tuple(local_orphans),
        )
