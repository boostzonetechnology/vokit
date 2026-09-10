from __future__ import annotations

import logging
from dataclasses import dataclass

from control_plane.billing.application.ports import InvoiceIndexRepository
from control_plane.billing.domain.types import InvoiceStatus
from control_plane.commission.application.accrue import AccrueCommission
from control_plane.commission.application.ports import LedgerRepository, PayoutRepository
from control_plane.commission.domain.types import LedgerKind, PayoutStatus
from shared_kernel.logging import log_event
from tenant.billing.service import TenantBillingService

logger = logging.getLogger("vokit.commission")


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    invoices_paid: int
    commissions_missing: int
    commissions_repaired: int
    payouts_unbalanced: int
    mismatches: tuple[str, ...]


class ReconcileFinance:
    def __init__(
        self,
        invoices: InvoiceIndexRepository,
        ledger: LedgerRepository,
        payouts: PayoutRepository,
        billing: TenantBillingService,
        accrue: AccrueCommission,
    ) -> None:
        self._invoices = invoices
        self._ledger = ledger
        self._payouts = payouts
        self._billing = billing
        self._accrue = accrue

    def execute(self) -> ReconciliationReport:
        mismatches: list[str] = []
        paid = self._invoices.list(status=InvoiceStatus.PAID)
        missing = 0
        repaired = 0
        for invoice in paid:
            tenant_invoice = self._billing.get_invoice(invoice.tenant_id, invoice.invoice_id)
            if tenant_invoice is None:
                mismatches.append(f"invoice:{invoice.invoice_id}:missing_tenant_row")
                continue
            payments = self._billing.list_payments(invoice.tenant_id, invoice.invoice_id)
            captured = [row for row in payments if row.status.value == "captured"]
            if not captured:
                mismatches.append(f"invoice:{invoice.invoice_id}:missing_payment")
                continue
            payment = captured[0]
            earned = self._ledger.get_earned_by_payment(payment.payment_id)
            if earned is None:
                missing += 1
                created = self._accrue.on_captured_payment(
                    payment=payment,
                    invoice=tenant_invoice,
                    settled_at=invoice.paid_at or payment.created_at,
                )
                if created is not None:
                    repaired += 1
                    mismatches.append(f"payment:{payment.payment_id}:commission_repaired")
        unbalanced = 0
        for payout in self._payouts.list():
            rows = [
                row
                for row in self._ledger.list_for_tenant(payout.tenant_id)
                if row.payout_id == payout.id
            ]
            reserved = any(row.kind is LedgerKind.PAYOUT_RESERVED for row in rows)
            paid_entry = any(row.kind is LedgerKind.PAYOUT_PAID for row in rows)
            if payout.status is PayoutStatus.PAID and (not reserved or not paid_entry):
                unbalanced += 1
                mismatches.append(f"payout:{payout.id}:ledger_gap")
            if payout.status is PayoutStatus.PAID and not payout.receipt_number:
                unbalanced += 1
                mismatches.append(f"payout:{payout.id}:missing_receipt")
        report = ReconciliationReport(
            invoices_paid=len(paid),
            commissions_missing=missing,
            commissions_repaired=repaired,
            payouts_unbalanced=unbalanced,
            mismatches=tuple(mismatches),
        )
        log_event(
            logger,
            "finance.reconciled",
            outcome="mismatch" if mismatches else "success",
            invoices_paid=report.invoices_paid,
            commissions_missing=missing,
            payouts_unbalanced=unbalanced,
        )
        return report
