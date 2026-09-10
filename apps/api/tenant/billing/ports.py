from __future__ import annotations

import uuid
from typing import Protocol

from tenant.billing.domain import (
    InvoiceRecord,
    MinuteLotRecord,
    PaymentRecord,
    SubscriptionRecord,
)
from tenant.runtime.ports import TenantConnection


class TenantBillingStore(Protocol):
    def put_subscription(
        self, connection: TenantConnection, subscription: SubscriptionRecord
    ) -> None: ...

    def get_subscription(
        self, connection: TenantConnection, subscription_id: uuid.UUID
    ) -> SubscriptionRecord | None: ...

    def get_active_subscription(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> SubscriptionRecord | None: ...

    def put_invoice(self, connection: TenantConnection, invoice: InvoiceRecord) -> None: ...

    def get_invoice(
        self, connection: TenantConnection, invoice_id: uuid.UUID
    ) -> InvoiceRecord | None: ...

    def list_invoices(
        self, connection: TenantConnection, customer_id: uuid.UUID | None = None
    ) -> list[InvoiceRecord]: ...

    def put_payment(self, connection: TenantConnection, payment: PaymentRecord) -> None: ...

    def list_payments(
        self, connection: TenantConnection, invoice_id: uuid.UUID | None = None
    ) -> list[PaymentRecord]: ...

    def put_lot(self, connection: TenantConnection, lot: MinuteLotRecord) -> None: ...

    def list_lots(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> list[MinuteLotRecord]: ...
