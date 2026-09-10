from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from control_plane.commission.application.ports import LedgerEntryRecord, LedgerRepository
from control_plane.commission.domain.policies import (
    commission_amount,
    eligible_base_from_lines,
    hold_available_at,
)
from control_plane.commission.domain.types import LedgerKind
from control_plane.tenancy.application.ports import TenantRepository
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.billing.domain import InvoiceRecord, PaymentRecord

logger = logging.getLogger("vokit.commission")


@dataclass(frozen=True, slots=True)
class AccrueCommand:
    payment: PaymentRecord
    invoice: InvoiceRecord
    settled_at: datetime


class AccrueCommission:
    def __init__(
        self,
        ledger: LedgerRepository,
        tenants: TenantRepository,
        hold_days: int | None = None,
    ) -> None:
        self._ledger = ledger
        self._tenants = tenants
        self._hold_days = hold_days

    def on_captured_payment(
        self,
        *,
        payment: PaymentRecord,
        invoice: InvoiceRecord,
        settled_at: datetime,
    ) -> LedgerEntryRecord | None:
        return self.execute(
            AccrueCommand(payment=payment, invoice=invoice, settled_at=settled_at)
        )

    def execute(self, command: AccrueCommand) -> LedgerEntryRecord | None:
        existing = self._ledger.get_earned_by_payment(command.payment.payment_id)
        if existing is not None:
            return existing
        tenant = self._tenants.get(command.invoice.tenant_id)
        if tenant is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        lines = tuple(
            (line.kind, line.amount_minor, line.currency, line.commissionable)
            for line in command.invoice.lines
        )
        base = eligible_base_from_lines(lines)
        amount = commission_amount(base, tenant.commission_rate_bps)
        if amount.minor_units < 1:
            return None
        entry_id = new_uuid7()
        entry = LedgerEntryRecord(
            id=entry_id,
            tenant_id=command.invoice.tenant_id,
            customer_id=command.invoice.customer_id,
            kind=LedgerKind.COMMISSION_EARNED,
            amount_minor=amount.minor_units,
            currency=amount.currency,
            payment_id=command.payment.payment_id,
            invoice_id=command.invoice.invoice_id,
            commission_id=entry_id,
            payout_id=None,
            eligible_base_minor=base.minor_units,
            rate_bps_snapshot=tenant.commission_rate_bps,
            earned_at=command.settled_at,
            available_at=hold_available_at(command.settled_at, self._hold_days),
            reason="captured_payment",
            actor_id=None,
            created_at=command.settled_at,
        )
        try:
            self._ledger.append(entry)
        except DomainError as exc:
            if exc.code == "ledger_duplicate":
                return self._ledger.get_earned_by_payment(command.payment.payment_id)
            raise
        log_event(
            logger,
            "commission.earned",
            outcome="success",
            tenant_id=str(entry.tenant_id),
            customer_id=str(entry.customer_id),
            invoice_id=str(entry.invoice_id),
            payment_id=str(entry.payment_id),
        )
        return entry
