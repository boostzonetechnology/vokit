from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.audit.application.record import RecordAudit, RecordAuditCommand
from control_plane.billing.domain.lots import LotBalance, drain_lots, remaining_minutes
from control_plane.billing.domain.types import LotKind
from control_plane.customers.application.ports import CustomerIndexRepository
from control_plane.customers.domain.policies import customer_not_found
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.billing.domain import MinuteLotRecord
from tenant.billing.service import TenantBillingService

logger = logging.getLogger("vokit.billing")

# Manual platform adjustments are not tied to an invoice settlement.
ADJUSTMENT_INVOICE_ID = uuid.UUID(int=0)


@dataclass(frozen=True, slots=True)
class AdjustCustomerMinutesCommand:
    customer_id: uuid.UUID
    minutes: int
    reason: str
    actor_id: uuid.UUID | None
    actor_role: str


@dataclass(frozen=True, slots=True)
class CustomerUsageSnapshot:
    remaining_minutes: int
    lots: list[MinuteLotRecord]


class GetCustomerUsage:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        billing: TenantBillingService,
    ) -> None:
        self._customers = customers
        self._billing = billing

    def execute(self, customer_id: uuid.UUID) -> CustomerUsageSnapshot:
        indexed = self._customers.get(customer_id)
        if indexed is None:
            raise customer_not_found()
        lots = self._billing.list_lots(indexed.tenant_id, customer_id)
        balances = tuple(
            LotBalance(
                lot_id=str(lot.lot_id),
                kind=lot.kind,
                remaining_minutes=lot.remaining_minutes,
            )
            for lot in lots
        )
        return CustomerUsageSnapshot(
            remaining_minutes=remaining_minutes(balances),
            lots=lots,
        )


class AdjustCustomerMinutes:
    def __init__(
        self,
        customers: CustomerIndexRepository,
        billing: TenantBillingService,
        clock: Clock,
        audit: RecordAudit,
    ) -> None:
        self._customers = customers
        self._billing = billing
        self._clock = clock
        self._audit = audit

    def execute(self, command: AdjustCustomerMinutesCommand) -> CustomerUsageSnapshot:
        if type(command.minutes) is not int or command.minutes == 0:
            raise DomainError(
                "validation_error",
                "minutes must be a non-zero integer.",
            )
        reason = command.reason.strip()
        if not reason:
            raise DomainError("validation_error", "reason is required.")
        indexed = self._customers.get(command.customer_id)
        if indexed is None:
            raise customer_not_found()
        now = self._clock.now()
        before = GetCustomerUsage(self._customers, self._billing).execute(command.customer_id)
        if command.minutes > 0:
            self._billing.put_lot(
                indexed.tenant_id,
                MinuteLotRecord(
                    lot_id=new_uuid7(),
                    tenant_id=indexed.tenant_id,
                    customer_id=command.customer_id,
                    invoice_id=ADJUSTMENT_INVOICE_ID,
                    kind=LotKind.ADJUSTMENT,
                    granted_minutes=command.minutes,
                    remaining_minutes=command.minutes,
                    created_at=now,
                ),
            )
        else:
            balances = tuple(
                LotBalance(
                    lot_id=str(lot.lot_id),
                    kind=lot.kind,
                    remaining_minutes=lot.remaining_minutes,
                )
                for lot in before.lots
            )
            drains = drain_lots(balances, abs(command.minutes))
            by_id = {lot.lot_id: lot for lot in before.lots}
            for drain in drains:
                lot = by_id[uuid.UUID(drain.lot_id)]
                self._billing.put_lot(
                    indexed.tenant_id,
                    MinuteLotRecord(
                        lot_id=lot.lot_id,
                        tenant_id=lot.tenant_id,
                        customer_id=lot.customer_id,
                        invoice_id=lot.invoice_id,
                        kind=lot.kind,
                        granted_minutes=lot.granted_minutes,
                        remaining_minutes=lot.remaining_minutes - drain.minutes,
                        created_at=lot.created_at,
                    ),
                )
        after = GetCustomerUsage(self._customers, self._billing).execute(command.customer_id)
        self._audit.execute(
            RecordAuditCommand(
                action="customer.minutes.adjusted",
                entity_type="customer",
                entity_id=str(command.customer_id),
                actor_id=command.actor_id,
                actor_role=command.actor_role,
                tenant_id=indexed.tenant_id,
                customer_id=command.customer_id,
                reason=reason,
                before_summary=str(before.remaining_minutes),
                after_summary=str(after.remaining_minutes),
                payload={"delta_minutes": command.minutes},
            )
        )
        log_event(
            logger,
            "customer.minutes.adjusted",
            outcome="success",
            tenant_id=str(indexed.tenant_id),
            customer_id=str(command.customer_id),
            delta_minutes=command.minutes,
        )
        return after
