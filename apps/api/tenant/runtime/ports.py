from __future__ import annotations

import uuid
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from control_plane.tenancy.application.ports import TenantDatabaseRecord
from tenant.runtime.domain import IsolationRecord


@dataclass(frozen=True, slots=True)
class ConnectionTarget:
    tenant_id: uuid.UUID
    database_id: uuid.UUID
    host: str
    port: int
    name: str
    secret_ref: str
    tls_required: bool


class TenantConnection(Protocol):
    tenant_id: uuid.UUID
    database_id: uuid.UUID

    def ping(self) -> None: ...


class TenantConnectionFactory(Protocol):
    def open(self, target: ConnectionTarget) -> TenantConnection: ...
    def close(self, connection: TenantConnection) -> None: ...


class TenantPool(Protocol):
    def acquire(self, target: ConnectionTarget) -> TenantConnection: ...
    def release(self, connection: TenantConnection) -> None: ...
    def discard(self, tenant_id: uuid.UUID) -> None: ...
    def checked_out_tenant_ids(self) -> set[uuid.UUID]: ...


class IsolationRecordRepository(Protocol):
    def upsert(self, connection: TenantConnection, record: IsolationRecord) -> None: ...
    def get(
        self, connection: TenantConnection, object_id: uuid.UUID
    ) -> IsolationRecord | None: ...


class SchemaRunner(Protocol):
    def current_version(self, connection: TenantConnection) -> str: ...
    def apply(self, connection: TenantConnection, target_version: str) -> str: ...
    def verify(self, connection: TenantConnection, expected_version: str) -> None: ...


class DatabaseAdministrator(Protocol):
    def ensure_database(self, target: ConnectionTarget) -> None: ...


class ConnectionGuard(Protocol):
    def bound(
        self, connection: TenantConnection, tenant_id: uuid.UUID
    ) -> AbstractContextManager[TenantConnection]: ...


def target_from_record(record: TenantDatabaseRecord) -> ConnectionTarget:
    return ConnectionTarget(
        tenant_id=record.tenant_id,
        database_id=record.id,
        host=record.host,
        port=record.port,
        name=record.name,
        secret_ref=record.secret_ref,
        tls_required=record.tls_required,
    )
