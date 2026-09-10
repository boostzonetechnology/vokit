from __future__ import annotations

import uuid

from control_plane.integrations.application.ports import (
    ConnectionIndexRecord,
    EndpointIndexRecord,
)
from control_plane.integrations.domain.types import ConnectionStatus, ProviderKind
from control_plane.integrations.models import (
    IntegrationConnectionIndex,
    WebhookEndpointIndex,
)


class DjangoConnectionIndexRepository:
    def save(self, record: ConnectionIndexRecord) -> None:
        IntegrationConnectionIndex.objects.update_or_create(
            id=record.connection_id,
            defaults={
                "tenant_id": record.tenant_id,
                "customer_id": record.customer_id,
                "provider": record.provider.value,
                "status": record.status.value,
            },
        )

    def get(self, connection_id: uuid.UUID) -> ConnectionIndexRecord | None:
        row = IntegrationConnectionIndex.objects.filter(id=connection_id).first()
        return self._to_record(row) if row else None

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[ConnectionIndexRecord]:
        rows = IntegrationConnectionIndex.objects.all()
        if tenant_id is not None:
            rows = rows.filter(tenant_id=tenant_id)
        if customer_id is not None:
            rows = rows.filter(customer_id=customer_id)
        return [self._to_record(row) for row in rows.order_by("-created_at")]

    def _to_record(self, row: IntegrationConnectionIndex) -> ConnectionIndexRecord:
        return ConnectionIndexRecord(
            connection_id=row.id,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            provider=ProviderKind(row.provider),
            status=ConnectionStatus(row.status),
        )


class DjangoEndpointIndexRepository:
    def save(self, record: EndpointIndexRecord) -> None:
        WebhookEndpointIndex.objects.update_or_create(
            id=record.endpoint_id,
            defaults={
                "tenant_id": record.tenant_id,
                "customer_id": record.customer_id,
                "status": record.status,
            },
        )

    def get(self, endpoint_id: uuid.UUID) -> EndpointIndexRecord | None:
        row = WebhookEndpointIndex.objects.filter(id=endpoint_id).first()
        return self._to_record(row) if row else None

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[EndpointIndexRecord]:
        rows = WebhookEndpointIndex.objects.all()
        if tenant_id is not None:
            rows = rows.filter(tenant_id=tenant_id)
        if customer_id is not None:
            rows = rows.filter(customer_id=customer_id)
        return [self._to_record(row) for row in rows.order_by("-created_at")]

    def _to_record(self, row: WebhookEndpointIndex) -> EndpointIndexRecord:
        return EndpointIndexRecord(
            endpoint_id=row.id,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            status=row.status,
        )
