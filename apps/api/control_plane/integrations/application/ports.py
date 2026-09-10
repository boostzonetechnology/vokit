from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from control_plane.integrations.domain.types import ConnectionStatus, ProviderKind


@dataclass(frozen=True, slots=True)
class ConnectionIndexRecord:
    connection_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    provider: ProviderKind
    status: ConnectionStatus


@dataclass(frozen=True, slots=True)
class EndpointIndexRecord:
    endpoint_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    status: str


class ConnectionIndexRepository(Protocol):
    def save(self, record: ConnectionIndexRecord) -> None: ...
    def get(self, connection_id: uuid.UUID) -> ConnectionIndexRecord | None: ...
    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[ConnectionIndexRecord]: ...


class EndpointIndexRepository(Protocol):
    def save(self, record: EndpointIndexRecord) -> None: ...
    def get(self, endpoint_id: uuid.UUID) -> EndpointIndexRecord | None: ...
    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[EndpointIndexRecord]: ...


class SecretVault(Protocol):
    def put(self, secret_ref: str, value: str) -> None: ...
    def get(self, secret_ref: str) -> str: ...
    def delete(self, secret_ref: str) -> None: ...


class IntegrationAdapter(Protocol):
    def execute(
        self,
        *,
        provider: ProviderKind,
        action: str,
        customer_id: str,
        arguments: dict,
        credential: str,
    ) -> dict[str, object]: ...


class WebhookTransport(Protocol):
    def post(
        self, *, url: str, headers: dict[str, str], body: bytes
    ) -> tuple[int, str]: ...
