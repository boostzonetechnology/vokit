from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, replace

from control_plane.customers.domain.types import CustomerStatus
from control_plane.telephony.application.expiry import expire_number_if_stale
from control_plane.telephony.application.ports import (
    PhoneNumberRepository,
    ReservationRecord,
    ReservationRepository,
)
from control_plane.telephony.domain.policies import (
    assert_available_for_reserve,
    number_not_found,
    number_reserved,
    reservation_deadline,
    reservation_is_active,
)
from control_plane.telephony.domain.types import NumberStatus, ReservationStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.agents.service import TenantAgentService
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.telephony")


@dataclass(frozen=True, slots=True)
class ReserveNumberCommand:
    tenant_id: uuid.UUID
    agent_id: uuid.UUID
    number_id: uuid.UUID
    reservation_seconds: int


class ReserveNumber:
    def __init__(
        self,
        numbers: PhoneNumberRepository,
        reservations: ReservationRepository,
        agents: TenantAgentService,
        lifecycle: TenantLifecycleService,
        clock: Clock,
    ) -> None:
        self._numbers = numbers
        self._reservations = reservations
        self._agents = agents
        self._lifecycle = lifecycle
        self._clock = clock

    def execute(self, command: ReserveNumberCommand) -> ReservationRecord:
        now = self._clock.now()
        with self._numbers.transaction():
            return self._reserve(command, now)

    def _reserve(self, command: ReserveNumberCommand, now):
        locked = self._numbers.lock(command.number_id)
        if locked is None:
            raise number_not_found()
        current = expire_number_if_stale(self._numbers, self._reservations, locked, now)
        if current.status is NumberStatus.RESERVED:
            existing = (
                self._reservations.get(current.reservation_id)
                if current.reservation_id
                else None
            )
            if (
                existing is not None
                and existing.tenant_id == command.tenant_id
                and reservation_is_active(
                    status=existing.status, expires_at=existing.expires_at, now=now
                )
            ):
                return existing
            raise number_reserved()
        assert_available_for_reserve(status=current.status)
        agent = self._agents.get_agent(command.tenant_id, command.agent_id)
        if agent is None or agent.tenant_id != command.tenant_id:
            raise number_not_found()
        customer = self._lifecycle.get_customer(command.tenant_id, agent.customer_id)
        if customer is None or customer.status is not CustomerStatus.ACTIVE:
            raise DomainError(
                "customer_inactive",
                "Customer is not active.",
                http_status=409,
            )
        reservation = ReservationRecord(
            id=new_uuid7(),
            number_id=current.id,
            tenant_id=command.tenant_id,
            customer_id=agent.customer_id,
            agent_id=agent.agent_id,
            status=ReservationStatus.ACTIVE,
            expires_at=reservation_deadline(now, seconds=command.reservation_seconds),
            created_at=now,
        )
        stored = self._reservations.save(reservation)
        self._numbers.save(
            replace(
                current,
                status=NumberStatus.RESERVED,
                reservation_id=stored.id,
                reserved_until=stored.expires_at,
                assigned_tenant_id=None,
                assigned_customer_id=None,
                assigned_agent_id=None,
                updated_at=now,
            )
        )
        log_event(
            logger,
            "telephony.number.reserved",
            outcome="success",
            tenant_id=str(command.tenant_id),
            number_id=str(current.id),
            reservation_id=str(stored.id),
        )
        return stored
