from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.billing.application.ports import (
    BillingIdempotencyRepository,
    IdempotencyRecord,
    InvoiceIndexRecord,
    InvoiceIndexRepository,
    PlanVersionRepository,
)
from control_plane.billing.domain.policies import assert_invoice_total, line_is_commissionable
from control_plane.billing.domain.types import InvoiceStatus, LineKind
from control_plane.risk.application.gate import CustomerRiskGate
from control_plane.tenancy.application.ports import Clock
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from shared_kernel.money import Money
from tenant.billing.domain import InvoiceLineRecord, InvoiceRecord
from tenant.billing.service import TenantBillingService

logger = logging.getLogger("vokit.billing")


@dataclass(frozen=True, slots=True)
class CreateTopUpCommand:
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    actor_id: uuid.UUID
    idempotency_key: str


class CreateTopUp:
    def __init__(
        self,
        versions: PlanVersionRepository,
        invoices: InvoiceIndexRepository,
        keys: BillingIdempotencyRepository,
        billing: TenantBillingService,
        clock: Clock,
        gate: CustomerRiskGate,
    ) -> None:
        self._versions = versions
        self._invoices = invoices
        self._keys = keys
        self._billing = billing
        self._clock = clock
        self._gate = gate

    def execute(self, command: CreateTopUpCommand) -> InvoiceRecord:
        key = command.idempotency_key.strip()
        if not key:
            raise DomainError("validation_error", "Idempotency-Key is required.")
        replay = self._keys.get(command.actor_id, key)
        if replay is not None:
            invoice = self._billing.get_invoice(command.tenant_id, replay.resource_id)
            if invoice is None:
                raise DomainError("not_found", "Resource not found.", http_status=404)
            return invoice
        self._gate.assert_open(command.customer_id)
        subscription = self._billing.get_active_subscription(
            command.tenant_id, command.customer_id
        )
        if subscription is None:
            raise DomainError(
                "subscription_required",
                "An active subscription is required before a top-up.",
                http_status=409,
            )
        version = self._versions.get(subscription.plan_version_id)
        if version is None or not version.allow_topups:
            raise DomainError(
                "topup_not_permitted",
                "This plan does not permit minute top-ups.",
                http_status=409,
            )
        now = self._clock.now()
        line = InvoiceLineRecord(
            line_id=new_uuid7(),
            kind=LineKind.TOPUP,
            description="Minute top-up",
            amount_minor=version.topup_price.minor_units,
            currency=version.topup_price.currency,
            minutes=version.topup_minutes,
            commissionable=line_is_commissionable(LineKind.TOPUP),
        )
        total = Money(line.amount_minor, line.currency)
        assert_invoice_total((total,), total)
        invoice = InvoiceRecord(
            invoice_id=new_uuid7(),
            tenant_id=command.tenant_id,
            customer_id=command.customer_id,
            subscription_id=subscription.subscription_id,
            status=InvoiceStatus.OPEN,
            currency=total.currency,
            total_minor=total.minor_units,
            lines=(line,),
            created_at=now,
            updated_at=now,
            paid_at=None,
        )
        stored = self._billing.put_invoice(command.tenant_id, invoice)
        self._invoices.create(
            InvoiceIndexRecord(
                invoice_id=stored.invoice_id,
                tenant_id=command.tenant_id,
                customer_id=command.customer_id,
                status=stored.status,
                total=Money(stored.total_minor, stored.currency),
                created_at=now,
                paid_at=None,
            )
        )
        self._keys.create(
            IdempotencyRecord(
                actor_id=command.actor_id,
                key=key,
                kind="topup",
                resource_id=stored.invoice_id,
            )
        )
        log_event(
            logger,
            "billing.topup.created",
            outcome="success",
            tenant_id=str(command.tenant_id),
            customer_id=str(command.customer_id),
            invoice_id=str(stored.invoice_id),
        )
        return stored
