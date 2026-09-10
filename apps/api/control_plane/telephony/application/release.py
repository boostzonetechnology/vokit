from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, replace

from control_plane.telephony.application.expiry import expire_number_if_stale
from control_plane.telephony.application.ports import (
    NumberProvider,
    PhoneNumberRecord,
    PhoneNumberRepository,
    ReservationRepository,
)
from control_plane.telephony.domain.policies import (
    assert_release_confirmed,
    number_not_found,
)
from control_plane.telephony.domain.types import (
    AssignmentStatus,
    NumberStatus,
    ReservationStatus,
)
from control_plane.tenancy.application.ports import Clock
from shared_kernel.logging import log_event
from tenant.numbers.service import TenantNumberService

logger = logging.getLogger("vokit.telephony")


@dataclass(frozen=True, slots=True)
class ReleaseNumberCommand:
    number_id: uuid.UUID
    tenant_id: uuid.UUID | None
    confirm: bool
    privileged: bool = False
    provider_release: bool = False


class ReleaseNumber:
    def __init__(
        self,
        numbers: PhoneNumberRepository,
        reservations: ReservationRepository,
        assignments: TenantNumberService,
        provider: NumberProvider,
        clock: Clock,
    ) -> None:
        self._numbers = numbers
        self._reservations = reservations
        self._assignments = assignments
        self._provider = provider
        self._clock = clock

    def execute(self, command: ReleaseNumberCommand) -> PhoneNumberRecord:
        assert_release_confirmed(command.confirm)
        now = self._clock.now()
        with self._numbers.transaction():
            return self._release(command, now)

    def _release(self, command: ReleaseNumberCommand, now):
        locked = self._numbers.lock(command.number_id)
        if locked is None:
            raise number_not_found()
        current = expire_number_if_stale(self._numbers, self._reservations, locked, now)
        if not command.privileged:
            if command.tenant_id is None:
                raise number_not_found()
            reserved_here = (
                current.status is NumberStatus.RESERVED
                and current.reservation_id is not None
            )
            assigned_here = (
                current.status is NumberStatus.ASSIGNED
                and current.assigned_tenant_id == command.tenant_id
            )
            if reserved_here:
                reservation = self._reservations.get(current.reservation_id)
                if reservation is None or reservation.tenant_id != command.tenant_id:
                    raise number_not_found()
            elif not assigned_here:
                raise number_not_found()
        if current.status is NumberStatus.RESERVED and current.reservation_id:
            reservation = self._reservations.get(current.reservation_id)
            if reservation is not None:
                self._reservations.save(
                    replace(reservation, status=ReservationStatus.CANCELLED)
                )
        if current.status is NumberStatus.ASSIGNED and current.assigned_tenant_id:
            assignment = self._assignments.active_for_number(
                current.assigned_tenant_id, current.id
            )
            if assignment is not None:
                self._assignments.put_assignment(
                    current.assigned_tenant_id,
                    replace(
                        assignment,
                        status=AssignmentStatus.RELEASED,
                        released_at=now,
                    ),
                )
        releasing = replace(current, status=NumberStatus.RELEASING, updated_at=now)
        self._numbers.save(releasing)
        if command.provider_release and current.provider_ref:
            self._provider.release(provider_ref=current.provider_ref)
            final_status = NumberStatus.RELEASED
        else:
            final_status = NumberStatus.AVAILABLE
        stored = self._numbers.save(
            replace(
                releasing,
                status=final_status,
                assigned_tenant_id=None,
                assigned_customer_id=None,
                assigned_agent_id=None,
                reservation_id=None,
                reserved_until=None,
                updated_at=now,
            )
        )
        log_event(
            logger,
            "telephony.number.released",
            outcome="success",
            number_id=str(current.id),
            status=final_status.value,
        )
        return stored
