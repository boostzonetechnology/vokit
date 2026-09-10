from __future__ import annotations

import uuid
from dataclasses import dataclass

from control_plane.billing.application.ports import (
    BillingIdempotencyRepository,
    IdempotencyRecord,
)
from control_plane.billing.domain.policies import invoice_not_found
from control_plane.billing.domain.types import InvoiceStatus, ProcessorSlug
from control_plane.ops.application.live_flags import assert_billing_live
from control_plane.risk.application.gate import CustomerRiskGate
from shared_kernel.errors import DomainError
from tenant.billing.domain import InvoiceRecord
from tenant.billing.service import TenantBillingService


@dataclass(frozen=True, slots=True)
class PayInvoiceCommand:
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    invoice_id: uuid.UUID
    actor_id: uuid.UUID
    idempotency_key: str
    processor: str


@dataclass(frozen=True, slots=True)
class CheckoutIntent:
    invoice: InvoiceRecord
    processor: str
    client_reference: str


class PayInvoice:
    def __init__(
        self,
        keys: BillingIdempotencyRepository,
        billing: TenantBillingService,
        gate: CustomerRiskGate,
    ) -> None:
        self._keys = keys
        self._billing = billing
        self._gate = gate

    def execute(self, command: PayInvoiceCommand) -> CheckoutIntent:
        self._gate.assert_open(command.customer_id)
        key = command.idempotency_key.strip()
        if not key:
            raise DomainError("validation_error", "Idempotency-Key is required.")
        try:
            processor = ProcessorSlug(command.processor)
        except ValueError as exc:
            raise DomainError("validation_error", "processor is invalid.") from exc
        invoice = self._billing.get_invoice(command.tenant_id, command.invoice_id)
        if invoice is None or invoice.customer_id != command.customer_id:
            raise invoice_not_found()
        if invoice.status is not InvoiceStatus.OPEN:
            raise DomainError(
                "invoice_not_payable",
                "Only open invoices can be paid.",
                http_status=409,
            )
        replay = self._keys.get(command.actor_id, key)
        if replay is not None:
            return CheckoutIntent(
                invoice=invoice,
                processor=processor.value,
                client_reference=f"pay_{replay.resource_id.hex}",
            )
        assert_billing_live()
        self._keys.create(
            IdempotencyRecord(
                actor_id=command.actor_id,
                key=key,
                kind="pay",
                resource_id=invoice.invoice_id,
            )
        )
        return CheckoutIntent(
            invoice=invoice,
            processor=processor.value,
            client_reference=f"pay_{invoice.invoice_id.hex}",
        )
