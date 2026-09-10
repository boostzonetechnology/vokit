from __future__ import annotations

import uuid

from shared_kernel.errors import DomainError
from tenant.billing.domain import (
    InvoiceRecord,
    MinuteLotRecord,
    PaymentRecord,
    SubscriptionRecord,
)
from tenant.billing.ports import TenantBillingStore
from tenant.runtime.router import TenantRouter


class TenantBillingService:
    def __init__(self, router: TenantRouter, store: TenantBillingStore) -> None:
        self._router = router
        self._store = store

    def put_subscription(
        self, tenant_id: uuid.UUID, subscription: SubscriptionRecord
    ) -> SubscriptionRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_subscription(connection, subscription)
            stored = self._store.get_subscription(connection, subscription.subscription_id)
        return self._require(stored)

    def get_subscription(
        self, tenant_id: uuid.UUID, subscription_id: uuid.UUID
    ) -> SubscriptionRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_subscription(connection, subscription_id)

    def get_active_subscription(
        self, tenant_id: uuid.UUID, customer_id: uuid.UUID
    ) -> SubscriptionRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_active_subscription(connection, customer_id)

    def put_invoice(self, tenant_id: uuid.UUID, invoice: InvoiceRecord) -> InvoiceRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_invoice(connection, invoice)
            stored = self._store.get_invoice(connection, invoice.invoice_id)
        return self._require(stored)

    def get_invoice(self, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> InvoiceRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_invoice(connection, invoice_id)

    def list_invoices(
        self, tenant_id: uuid.UUID, customer_id: uuid.UUID | None = None
    ) -> list[InvoiceRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_invoices(connection, customer_id)

    def put_payment(self, tenant_id: uuid.UUID, payment: PaymentRecord) -> PaymentRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_payment(connection, payment)
            rows = [
                row
                for row in self._store.list_payments(connection, payment.invoice_id)
                if row.payment_id == payment.payment_id
            ]
        if not rows:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return rows[0]

    def list_payments(
        self, tenant_id: uuid.UUID, invoice_id: uuid.UUID | None = None
    ) -> list[PaymentRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_payments(connection, invoice_id)

    def put_lot(self, tenant_id: uuid.UUID, lot: MinuteLotRecord) -> MinuteLotRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_lot(connection, lot)
            rows = [
                row
                for row in self._store.list_lots(connection, lot.customer_id)
                if row.lot_id == lot.lot_id
            ]
        if not rows:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return rows[0]

    def list_lots(self, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> list[MinuteLotRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_lots(connection, customer_id)

    def _require(self, stored):
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored
