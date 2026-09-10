from __future__ import annotations

import logging
from dataclasses import dataclass

from control_plane.billing.application.ports import InvoiceIndexRepository, NormalizedPaymentEvent
from control_plane.risk.application.ports import (
    RiskCaseRecord,
    RiskCaseRepository,
    RiskEventRecord,
    RiskEventRepository,
)
from control_plane.risk.domain.types import COMMERCIALLY_BLOCKED, RiskStatus
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.risk")


@dataclass(frozen=True, slots=True)
class RiskFlagResult:
    duplicate: bool
    status: str
    invoice_id: str
    customer_id: str | None


class FlagRiskyPayment:
    def __init__(
        self,
        events: RiskEventRepository,
        cases: RiskCaseRepository,
        invoices: InvoiceIndexRepository,
        clock: Clock,
    ) -> None:
        self._events = events
        self._cases = cases
        self._invoices = invoices
        self._clock = clock

    def execute(self, event: NormalizedPaymentEvent) -> RiskFlagResult:
        if not event.event_id.strip():
            raise DomainError("validation_error", "event_id is required.")
        existing = self._events.get(event.processor, event.event_id)
        if existing is not None:
            customer_id = str(existing.customer_id) if existing.customer_id else None
            return RiskFlagResult(True, "duplicate", str(event.invoice_id), customer_id)
        indexed = self._invoices.get(event.invoice_id)
        if indexed is None:
            self._events.create(
                RiskEventRecord(
                    processor=event.processor,
                    event_id=event.event_id,
                    customer_id=None,
                    kind="risk_flag",
                    status="rejected",
                )
            )
            raise DomainError("not_found", "Resource not found.", http_status=404)
        now = self._clock.now()
        case = self._cases.get_for_customer(indexed.customer_id)
        status = (
            case.status
            if case is not None and case.status in COMMERCIALLY_BLOCKED
            else RiskStatus.PAYMENT_REVIEW_REQUIRED
        )
        self._cases.upsert(
            RiskCaseRecord(
                id=case.id if case is not None else new_uuid7(),
                tenant_id=indexed.tenant_id,
                customer_id=indexed.customer_id,
                status=status,
                last_invoice_id=indexed.invoice_id,
                last_payment_id=case.last_payment_id if case is not None else None,
                last_event_id=event.event_id,
                note="payment_risk",
                permanently_banned=bool(case.permanently_banned) if case is not None else False,
                created_at=case.created_at if case is not None else now,
                updated_at=now,
            )
        )
        self._events.create(
            RiskEventRecord(
                processor=event.processor,
                event_id=event.event_id,
                customer_id=indexed.customer_id,
                kind="risk_flag",
                status="processed",
            )
        )
        log_event(
            logger,
            "risk.payment.flagged",
            outcome="success",
            tenant_id=str(indexed.tenant_id),
            customer_id=str(indexed.customer_id),
            invoice_id=str(indexed.invoice_id),
        )
        return RiskFlagResult(False, "processed", str(indexed.invoice_id), str(indexed.customer_id))
