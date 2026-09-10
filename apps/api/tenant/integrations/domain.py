from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from control_plane.integrations.domain.types import (
    ConnectionStatus,
    DeliveryStatus,
    EndpointStatus,
    ProviderKind,
)


@dataclass(frozen=True, slots=True)
class TenantConnectionRecord:
    connection_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    provider: ProviderKind
    status: ConnectionStatus
    secret_ref: str
    display_name: str
    created_at: datetime
    updated_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TenantIntegrationSettings:
    customer_id: uuid.UUID
    tenant_id: uuid.UUID
    self_service: bool
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class TenantWebhookEndpoint:
    endpoint_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    url: str
    secret_ref: str
    status: EndpointStatus
    events: tuple[str, ...]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class TenantWebhookDelivery:
    delivery_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    endpoint_id: uuid.UUID
    event_id: uuid.UUID
    event_type: str
    object_id: uuid.UUID
    status: DeliveryStatus
    attempt_count: int
    response_code: int | None
    last_error: str
    created_at: datetime
    next_attempt_at: datetime | None = None
    delivered_at: datetime | None = None
