from __future__ import annotations

import uuid
from typing import Protocol

from tenant.integrations.domain import (
    TenantConnectionRecord,
    TenantIntegrationSettings,
    TenantWebhookDelivery,
    TenantWebhookEndpoint,
)
from tenant.runtime.ports import TenantConnection


class TenantIntegrationStore(Protocol):
    def put_connection(self, connection: TenantConnection, row: TenantConnectionRecord) -> None: ...
    def get_connection(
        self, connection: TenantConnection, connection_id: uuid.UUID
    ) -> TenantConnectionRecord | None: ...
    def list_connections(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantConnectionRecord]: ...
    def put_settings(
        self, connection: TenantConnection, row: TenantIntegrationSettings
    ) -> None: ...
    def get_settings(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> TenantIntegrationSettings | None: ...
    def put_endpoint(self, connection: TenantConnection, row: TenantWebhookEndpoint) -> None: ...
    def get_endpoint(
        self, connection: TenantConnection, endpoint_id: uuid.UUID
    ) -> TenantWebhookEndpoint | None: ...
    def list_endpoints(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantWebhookEndpoint]: ...
    def put_delivery(self, connection: TenantConnection, row: TenantWebhookDelivery) -> None: ...
    def get_delivery(
        self, connection: TenantConnection, delivery_id: uuid.UUID
    ) -> TenantWebhookDelivery | None: ...
    def list_deliveries(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
        endpoint_id: uuid.UUID | None = None,
    ) -> list[TenantWebhookDelivery]: ...
