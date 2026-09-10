from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, replace

from control_plane.billing.application.ports import (
    BillingIdempotencyRepository,
    IdempotencyRecord,
    InvoiceIndexRecord,
    InvoiceIndexRepository,
)
from control_plane.billing.domain.policies import assert_invoice_total, line_is_commissionable
from control_plane.billing.domain.types import InvoiceStatus, LineKind
from control_plane.customers.domain.types import CustomerStatus
from control_plane.risk.application.gate import CustomerRiskGate
from control_plane.telephony.application.expiry import expire_number_if_stale
from control_plane.telephony.application.ports import (
    PhoneNumberRepository,
    ReservationRepository,
)
from control_plane.telephony.domain.policies import (
    assert_assign_confirmed,
    assert_one_routing_target,
    number_not_found,
    reservation_is_active,
)
from control_plane.telephony.domain.types import (
    AssignmentStatus,
    NumberStatus,
    ReservationStatus,
)
from control_plane.tenancy.application.ports import Clock, TenantRepository
from control_plane.tenancy.domain.lifecycle import assert_agency_may_purchase_numbers
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from shared_kernel.money import Money
from tenant.agents.service import TenantAgentService
from tenant.billing.domain import InvoiceLineRecord, InvoiceRecord
from tenant.billing.service import TenantBillingService
from tenant.lifecycle.service import TenantLifecycleService
from tenant.numbers.domain import NumberAssignmentRecord
from tenant.numbers.service import TenantNumberService

logger = logging.getLogger("vokit.telephony")


@dataclass(frozen=True, slots=True)
class AssignNumberCommand:
    tenant_id: uuid.UUID
    reservation_id: uuid.UUID
    actor_id: uuid.UUID
    confirm: bool
    idempotency_key: str
    privileged: bool = False


@dataclass(frozen=True, slots=True)
class AssignNumberResult:
    assignment: NumberAssignmentRecord
    invoice: InvoiceRecord


class AssignNumber:
    def __init__(
        self,
        numbers: PhoneNumberRepository,
        reservations: ReservationRepository,
        tenants: TenantRepository,
        agents: TenantAgentService,
        lifecycle: TenantLifecycleService,
        assignments: TenantNumberService,
        billing: TenantBillingService,
        invoices: InvoiceIndexRepository,
        keys: BillingIdempotencyRepository,
        gate: CustomerRiskGate,
        clock: Clock,
    ) -> None:
        self._numbers = numbers
        self._reservations = reservations
        self._tenants = tenants
        self._agents = agents
        self._lifecycle = lifecycle
        self._assignments = assignments
        self._billing = billing
        self._invoices = invoices
        self._keys = keys
        self._gate = gate
        self._clock = clock

    def execute(self, command: AssignNumberCommand) -> AssignNumberResult:
        key = command.idempotency_key.strip()
        if not key:
            raise DomainError("validation_error", "Idempotency-Key is required.")
        replay = self._keys.get(command.actor_id, key)
        if replay is not None:
            assignment = self._assignments.get_assignment(
                command.tenant_id, replay.resource_id
            )
            if assignment is None or assignment.invoice_id is None:
                raise number_not_found()
            invoice = self._billing.get_invoice(command.tenant_id, assignment.invoice_id)
            if invoice is None:
                raise number_not_found()
            return AssignNumberResult(assignment=assignment, invoice=invoice)
        assert_assign_confirmed(command.confirm)
        reservation = self._reservations.get(command.reservation_id)
        if reservation is None:
            raise number_not_found()
        if reservation.tenant_id != command.tenant_id and not command.privileged:
            raise number_not_found()
        now = self._clock.now()
        with self._numbers.transaction():
            return self._assign(command, reservation, key, now)

    def _assign(self, command: AssignNumberCommand, reservation, key: str, now):
        locked = self._numbers.lock(reservation.number_id)
        if locked is None:
            raise number_not_found()
        current = expire_number_if_stale(self._numbers, self._reservations, locked, now)
        reservation = self._reservations.get(command.reservation_id)
        if reservation is None or not reservation_is_active(
            status=reservation.status, expires_at=reservation.expires_at, now=now
        ):
            raise DomainError(
                "reservation_expired",
                "Reservation is no longer active.",
                http_status=409,
            )
        if current.reservation_id != reservation.id:
            raise number_not_found()
        existing = self._assignments.active_for_number(command.tenant_id, current.id)
        if existing is not None and existing.invoice_id is not None:
            invoice = self._billing.get_invoice(command.tenant_id, existing.invoice_id)
            if invoice is None:
                raise number_not_found()
            return AssignNumberResult(assignment=existing, invoice=invoice)
        tenant = self._tenants.get(command.tenant_id)
        if tenant is None:
            raise number_not_found()
        assert_agency_may_purchase_numbers(
            tenant.agency_status,
            tenant.capabilities,
            privileged=command.privileged,
        )
        agent = self._agents.get_agent(command.tenant_id, reservation.agent_id)
        if agent is None or agent.customer_id != reservation.customer_id:
            raise number_not_found()
        customer = self._lifecycle.get_customer(command.tenant_id, agent.customer_id)
        if customer is None or customer.status is not CustomerStatus.ACTIVE:
            raise DomainError(
                "customer_inactive",
                "Customer is not active.",
                http_status=409,
            )
        self._gate.assert_open(agent.customer_id)
        subscription = self._billing.get_active_subscription(
            command.tenant_id, agent.customer_id
        )
        if subscription is None:
            raise DomainError(
                "subscription_required",
                "An active subscription is required before assigning a number.",
                http_status=409,
            )
        assert_one_routing_target(assigned_agent_id=current.assigned_agent_id)
        line = InvoiceLineRecord(
            line_id=new_uuid7(),
            kind=LineKind.NUMBER,
            description=f"Phone number {current.e164}",
            amount_minor=current.monthly_cost.minor_units,
            currency=current.monthly_cost.currency,
            minutes=0,
            commissionable=line_is_commissionable(LineKind.NUMBER),
        )
        total = Money(line.amount_minor, line.currency)
        assert_invoice_total((total,), total)
        invoice = self._billing.put_invoice(
            command.tenant_id,
            InvoiceRecord(
                invoice_id=new_uuid7(),
                tenant_id=command.tenant_id,
                customer_id=agent.customer_id,
                subscription_id=subscription.subscription_id,
                status=InvoiceStatus.OPEN,
                currency=total.currency,
                total_minor=total.minor_units,
                lines=(line,),
                created_at=now,
                updated_at=now,
                paid_at=None,
            ),
        )
        self._invoices.create(
            InvoiceIndexRecord(
                invoice_id=invoice.invoice_id,
                tenant_id=command.tenant_id,
                customer_id=agent.customer_id,
                status=invoice.status,
                total=Money(invoice.total_minor, invoice.currency),
                created_at=now,
                paid_at=None,
            )
        )
        assignment = self._assignments.put_assignment(
            command.tenant_id,
            NumberAssignmentRecord(
                assignment_id=new_uuid7(),
                tenant_id=command.tenant_id,
                customer_id=agent.customer_id,
                agent_id=agent.agent_id,
                phone_number_id=current.id,
                e164=current.e164,
                status=AssignmentStatus.ASSIGNED,
                invoice_id=invoice.invoice_id,
                assigned_at=now,
            ),
        )
        self._reservations.save(replace(reservation, status=ReservationStatus.CONSUMED))
        self._numbers.save(
            replace(
                current,
                status=NumberStatus.ASSIGNED,
                assigned_tenant_id=command.tenant_id,
                assigned_customer_id=agent.customer_id,
                assigned_agent_id=agent.agent_id,
                reservation_id=None,
                reserved_until=None,
                updated_at=now,
            )
        )
        self._keys.create(
            IdempotencyRecord(
                actor_id=command.actor_id,
                key=key,
                kind="number_assign",
                resource_id=assignment.assignment_id,
            )
        )
        log_event(
            logger,
            "telephony.number.assigned",
            outcome="success",
            tenant_id=str(command.tenant_id),
            customer_id=str(agent.customer_id),
            number_id=str(current.id),
            invoice_id=str(invoice.invoice_id),
        )
        return AssignNumberResult(assignment=assignment, invoice=invoice)
