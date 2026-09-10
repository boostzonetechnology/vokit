from __future__ import annotations

import uuid

from shared_kernel.errors import DomainError
from tenant.integrations.domain import (
    TenantConnectionRecord,
    TenantIntegrationSettings,
    TenantWebhookDelivery,
    TenantWebhookEndpoint,
)
from tenant.integrations.ports import TenantIntegrationStore
from tenant.runtime.router import TenantRouter


class TenantIntegrationService:
    def __init__(self, router: TenantRouter, store: TenantIntegrationStore) -> None:
        self._router = router
        self._store = store

    def put_connection(
        self, tenant_id: uuid.UUID, row: TenantConnectionRecord
    ) -> TenantConnectionRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_connection(connection, row)
            stored = self._store.get_connection(connection, row.connection_id)
        return self._require(stored)

    def get_connection(
        self, tenant_id: uuid.UUID, connection_id: uuid.UUID
    ) -> TenantConnectionRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_connection(connection, connection_id)

    def list_connections(
        self, tenant_id: uuid.UUID, *, customer_id: uuid.UUID | None = None
    ) -> list[TenantConnectionRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_connections(connection, customer_id=customer_id)

    def put_settings(
        self, tenant_id: uuid.UUID, row: TenantIntegrationSettings
    ) -> TenantIntegrationSettings:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_settings(connection, row)
            stored = self._store.get_settings(connection, row.customer_id)
        return self._require(stored)

    def get_settings(
        self, tenant_id: uuid.UUID, customer_id: uuid.UUID
    ) -> TenantIntegrationSettings | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_settings(connection, customer_id)

    def put_endpoint(
        self, tenant_id: uuid.UUID, row: TenantWebhookEndpoint
    ) -> TenantWebhookEndpoint:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_endpoint(connection, row)
            stored = self._store.get_endpoint(connection, row.endpoint_id)
        return self._require(stored)

    def get_endpoint(
        self, tenant_id: uuid.UUID, endpoint_id: uuid.UUID
    ) -> TenantWebhookEndpoint | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_endpoint(connection, endpoint_id)

    def list_endpoints(
        self, tenant_id: uuid.UUID, *, customer_id: uuid.UUID | None = None
    ) -> list[TenantWebhookEndpoint]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_endpoints(connection, customer_id=customer_id)

    def put_delivery(
        self, tenant_id: uuid.UUID, row: TenantWebhookDelivery
    ) -> TenantWebhookDelivery:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_delivery(connection, row)
            stored = self._store.get_delivery(connection, row.delivery_id)
        return self._require(stored)

    def get_delivery(
        self, tenant_id: uuid.UUID, delivery_id: uuid.UUID
    ) -> TenantWebhookDelivery | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_delivery(connection, delivery_id)

    def list_deliveries(
        self,
        tenant_id: uuid.UUID,
        *,
        customer_id: uuid.UUID | None = None,
        endpoint_id: uuid.UUID | None = None,
    ) -> list[TenantWebhookDelivery]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_deliveries(
                connection, customer_id=customer_id, endpoint_id=endpoint_id
            )

    def _require(self, stored):
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored
