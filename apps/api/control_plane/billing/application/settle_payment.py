from __future__ import annotations

import logging
from dataclasses import dataclass, replace

from control_plane.billing.application.ports import (
    CommissionAccrual,
    InvoiceIndexRecord,
    InvoiceIndexRepository,
    NormalizedPaymentEvent,
    PlanVersionRepository,
    ProcessorEventRecord,
    ProcessorEventRepository,
)
from control_plane.billing.domain.entitlements import PENDING_UPGRADE
from control_plane.billing.domain.policies import invoice_not_found, payment_amount_mismatch
from control_plane.billing.domain.types import (
    InvoiceStatus,
    LineKind,
    LotKind,
    PaymentStatus,
    ProcessorEventStatus,
)
from control_plane.ops.application.live_flags import assert_billing_live
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from shared_kernel.money import Money
from tenant.billing.domain import InvoiceRecord, MinuteLotRecord, PaymentRecord
from tenant.billing.service import TenantBillingService

logger = logging.getLogger("vokit.billing")

_LINE_TO_LOT = {
    LineKind.SUBSCRIPTION: LotKind.INCLUDED,
    LineKind.TOPUP: LotKind.TOPUP,
    LineKind.OVERAGE: LotKind.OVERAGE,
}


def grant_invoice_lots(billing: TenantBillingService, invoice: InvoiceRecord, now) -> None:
    for line in invoice.lines:
        kind = _LINE_TO_LOT.get(line.kind)
        if kind is None or line.minutes < 1:
            continue
        billing.put_lot(
            invoice.tenant_id,
            MinuteLotRecord(
                lot_id=new_uuid7(),
                tenant_id=invoice.tenant_id,
                customer_id=invoice.customer_id,
                invoice_id=invoice.invoice_id,
                kind=kind,
                granted_minutes=line.minutes,
                remaining_minutes=line.minutes,
                created_at=now,
            ),
        )


@dataclass(frozen=True, slots=True)
class SettlementResult:
    duplicate: bool
    status: str
    invoice_id: str | None


class SettlePayment:
    def __init__(
        self,
        events: ProcessorEventRepository,
        invoices: InvoiceIndexRepository,
        billing: TenantBillingService,
        clock: Clock,
        accrual: CommissionAccrual | None = None,
        versions: PlanVersionRepository | None = None,
    ) -> None:
        self._events = events
        self._invoices = invoices
        self._billing = billing
        self._clock = clock
        self._accrual = accrual
        self._versions = versions

    def execute(self, event: NormalizedPaymentEvent) -> SettlementResult:
        if not event.event_id.strip():
            raise DomainError("validation_error", "event_id is required.")
        existing = self._events.get(event.processor, event.event_id)
        if existing is not None:
            invoice_id = str(existing.invoice_id) if existing.invoice_id else None
            return SettlementResult(True, existing.status.value, invoice_id)
        assert_billing_live()
        if not event.captured:
            self._events.create(
                ProcessorEventRecord(
                    processor=event.processor,
                    event_id=event.event_id,
                    invoice_id=event.invoice_id,
                    status=ProcessorEventStatus.REJECTED,
                )
            )
            indexed = self._invoices.get(event.invoice_id)
            if indexed is not None:
                from control_plane.notifications.application.hooks import billing_notify
                from control_plane.notifications.infrastructure.recipients import (
                    recipients_for_scope,
                )

                billing_notify(
                    event_type="payment.failure",
                    recipients=(
                        *recipients_for_scope(customer_id=indexed.customer_id),
                        *recipients_for_scope(tenant_id=indexed.tenant_id),
                    ),
                    variables={
                        "invoice_id": str(event.invoice_id),
                        "amount": str(event.amount.minor_units),
                    },
                    tenant_id=indexed.tenant_id,
                    customer_id=indexed.customer_id,
                )
            raise DomainError(
                "payment_not_captured",
                "Payment was not captured.",
                http_status=409,
            )
        indexed = self._invoices.get(event.invoice_id)
        if indexed is None:
            self._events.create(
                ProcessorEventRecord(
                    processor=event.processor,
                    event_id=event.event_id,
                    invoice_id=event.invoice_id,
                    status=ProcessorEventStatus.REJECTED,
                )
            )
            raise invoice_not_found()
        invoice = self._billing.get_invoice(indexed.tenant_id, event.invoice_id)
        if invoice is None:
            self._events.create(
                ProcessorEventRecord(
                    processor=event.processor,
                    event_id=event.event_id,
                    invoice_id=event.invoice_id,
                    status=ProcessorEventStatus.REJECTED,
                )
            )
            raise invoice_not_found()
        if invoice.status is InvoiceStatus.PAID:
            self._events.create(
                ProcessorEventRecord(
                    processor=event.processor,
                    event_id=event.event_id,
                    invoice_id=invoice.invoice_id,
                    status=ProcessorEventStatus.DUPLICATE,
                )
            )
            return SettlementResult(
                True,
                ProcessorEventStatus.DUPLICATE.value,
                str(invoice.invoice_id),
            )
        if invoice.status is not InvoiceStatus.OPEN:
            raise DomainError(
                "invoice_not_payable",
                "Only open invoices can be settled.",
                http_status=409,
            )
        if (
            event.amount.minor_units != invoice.total_minor
            or event.amount.currency != invoice.currency
        ):
            raise payment_amount_mismatch()
        now = self._clock.now()
        payment = PaymentRecord(
            payment_id=new_uuid7(),
            invoice_id=invoice.invoice_id,
            tenant_id=invoice.tenant_id,
            customer_id=invoice.customer_id,
            processor=event.processor,
            processor_event_id=event.event_id,
            amount_minor=event.amount.minor_units,
            currency=event.amount.currency,
            status=PaymentStatus.CAPTURED,
            created_at=now,
        )
        paid = replace(
            invoice,
            status=InvoiceStatus.PAID,
            updated_at=now,
            paid_at=now,
        )
        self._billing.put_payment(invoice.tenant_id, payment)
        self._billing.put_invoice(invoice.tenant_id, paid)
        grant_invoice_lots(self._billing, paid, now)
        self._apply_upgrade(paid, now)
        from control_plane.billing.application.customer_projection import (
            refresh_minutes_projection,
            refresh_plan_projection,
        )
        from control_plane.customers.infrastructure.container import customer_index

        index = customer_index()
        refresh_plan_projection(
            index, self._billing, paid.tenant_id, paid.customer_id
        )
        refresh_minutes_projection(
            index, self._billing, paid.tenant_id, paid.customer_id
        )
        self._invoices.update(
            InvoiceIndexRecord(
                invoice_id=paid.invoice_id,
                tenant_id=paid.tenant_id,
                customer_id=paid.customer_id,
                status=paid.status,
                total=Money(paid.total_minor, paid.currency),
                created_at=paid.created_at,
                paid_at=now,
            )
        )
        self._events.create(
            ProcessorEventRecord(
                processor=event.processor,
                event_id=event.event_id,
                invoice_id=paid.invoice_id,
                status=ProcessorEventStatus.PROCESSED,
            )
        )
        if self._accrual is not None:
            self._accrual.on_captured_payment(
                payment=payment, invoice=paid, settled_at=now
            )
        from control_plane.notifications.application.hooks import billing_notify
        from control_plane.notifications.infrastructure.recipients import (
            recipients_for_scope,
        )

        billing_notify(
            event_type="payment.success",
            recipients=(
                *recipients_for_scope(customer_id=paid.customer_id),
                *recipients_for_scope(tenant_id=paid.tenant_id),
            ),
            variables={
                "invoice_id": str(paid.invoice_id),
                "amount": str(paid.total_minor),
            },
            tenant_id=paid.tenant_id,
            customer_id=paid.customer_id,
        )
        log_event(
            logger,
            "billing.invoice.settled",
            outcome="success",
            tenant_id=str(paid.tenant_id),
            customer_id=str(paid.customer_id),
            invoice_id=str(paid.invoice_id),
            processor=event.processor,
        )
        return SettlementResult(False, ProcessorEventStatus.PROCESSED.value, str(paid.invoice_id))

    def _apply_upgrade(self, invoice: InvoiceRecord, now) -> None:
        if invoice.subscription_id is None or self._versions is None:
            return
        subscription = self._billing.get_subscription(
            invoice.tenant_id, invoice.subscription_id
        )
        if (
            subscription is None
            or subscription.pending_kind != PENDING_UPGRADE
            or subscription.pending_invoice_id != invoice.invoice_id
            or subscription.pending_plan_version_id is None
        ):
            return
        target = self._versions.get(subscription.pending_plan_version_id)
        if target is None:
            return
        switched = replace(
            subscription,
            plan_id=target.plan_id,
            plan_version_id=target.id,
            period_started_at=now,
            pending_plan_version_id=None,
            pending_kind=None,
            pending_invoice_id=None,
            pending_effective_at=None,
            updated_at=now,
        )
        self._billing.put_subscription(invoice.tenant_id, switched)
        if target.used_at is None:
            self._versions.update(replace(target, used_at=now))
