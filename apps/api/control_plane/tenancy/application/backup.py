from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass

from control_plane.tenancy.application.ports import (
    TenantDatabaseRepository,
    TenantRepository,
)
from control_plane.tenancy.domain.policies import tenant_unavailable
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event
from tenant.runtime.ports import TenantConnectionFactory, target_from_record

logger = logging.getLogger("vokit.tenancy")

FORBIDDEN_SNAPSHOT_KEYS = frozenset(
    {"password", "passwd", "dsn", "secret", "api_key", "token"}
)


@dataclass(frozen=True, slots=True)
class TenantSnapshot:
    tenant_id: uuid.UUID
    database_id: uuid.UUID
    database_name: str
    secret_ref: str
    schema_version: str
    payload: dict[str, object]

    def to_public_dict(self) -> dict[str, object]:
        return {
            "plane": "tenant",
            "tenant_id": str(self.tenant_id),
            "database_id": str(self.database_id),
            "database_name": self.database_name,
            "secret_ref": self.secret_ref,
            "schema_version": self.schema_version,
            "payload": self.payload,
        }


def snapshot_from_dict(raw: dict[str, object]) -> TenantSnapshot:
    if raw.get("plane") != "tenant":
        raise DomainError("validation_error", "Tenant snapshot is required.")
    payload = raw.get("payload")
    if not isinstance(payload, dict):
        raise DomainError("validation_error", "Snapshot payload is invalid.")
    return TenantSnapshot(
        tenant_id=uuid.UUID(str(raw.get("tenant_id"))),
        database_id=uuid.UUID(str(raw.get("database_id"))),
        database_name=str(raw.get("database_name") or ""),
        secret_ref=str(raw.get("secret_ref") or ""),
        schema_version=str(raw.get("schema_version") or ""),
        payload=payload,
    )


def assert_snapshot_has_no_secrets(document: dict[str, object]) -> None:
    raw = json.dumps(document)
    lowered = raw.lower()
    if "mysql://" in lowered or "postgres://" in lowered:
        raise DomainError("backup_secret_leak", "Snapshot must not contain a DSN.")
    for key in FORBIDDEN_SNAPSHOT_KEYS:
        if f'"{key}"' in lowered:
            raise DomainError("backup_secret_leak", "Snapshot must not contain secrets.")


class BackupTenant:
    def __init__(
        self,
        tenants: TenantRepository,
        databases: TenantDatabaseRepository,
        connections: TenantConnectionFactory,
    ) -> None:
        self._tenants = tenants
        self._databases = databases
        self._connections = connections

    def execute(self, tenant_id: uuid.UUID) -> TenantSnapshot:
        tenant = self._tenants.get(tenant_id)
        database = self._databases.get_for_tenant(tenant_id)
        if tenant is None or database is None:
            raise tenant_unavailable()
        target = target_from_record(database)
        connection = self._connections.open(target)
        try:
            payload = self._connections.export_snapshot(connection)
        finally:
            self._connections.close(connection)
        snapshot = TenantSnapshot(
            tenant_id=tenant.id,
            database_id=database.id,
            database_name=database.name,
            secret_ref=database.secret_ref,
            schema_version=database.schema_version,
            payload=payload,
        )
        assert_snapshot_has_no_secrets(snapshot.to_public_dict())
        log_event(
            logger,
            "tenant.backup.created",
            outcome="success",
            tenant_id=str(tenant.id),
            database_id=str(database.id),
        )
        return snapshot


class RestoreTenant:
    def __init__(
        self,
        tenants: TenantRepository,
        databases: TenantDatabaseRepository,
        connections: TenantConnectionFactory,
    ) -> None:
        self._tenants = tenants
        self._databases = databases
        self._connections = connections

    def execute(self, tenant_id: uuid.UUID, snapshot: TenantSnapshot) -> TenantSnapshot:
        if snapshot.tenant_id != tenant_id:
            raise DomainError(
                "tenant_restore_mismatch",
                "Snapshot does not belong to this tenant.",
                http_status=409,
            )
        tenant = self._tenants.get(tenant_id)
        database = self._databases.get_for_tenant(tenant_id)
        if tenant is None or database is None:
            raise tenant_unavailable()
        target = target_from_record(database)
        connection = self._connections.open(target)
        try:
            self._connections.restore_snapshot(connection, snapshot.payload)
        finally:
            self._connections.close(connection)
        log_event(
            logger,
            "tenant.restore.applied",
            outcome="success",
            tenant_id=str(tenant.id),
            database_id=str(database.id),
        )
        return snapshot


class BackupControlPlane:
    def __init__(self, tenants: TenantRepository, databases: TenantDatabaseRepository) -> None:
        self._tenants = tenants
        self._databases = databases

    def execute(self) -> dict[str, object]:
        rows = []
        for tenant in self._tenants.list():
            database = self._databases.get_for_tenant(tenant.id)
            rows.append(
                {
                    "tenant_id": str(tenant.id),
                    "display_name": tenant.display_name,
                    "status": tenant.status.value,
                    "agency_status": tenant.agency_status.value,
                    "secret_ref": database.secret_ref if database else "",
                    "database_name": database.name if database else "",
                    "schema_version": database.schema_version if database else "",
                }
            )
        document = {"plane": "control", "tenants": rows}
        assert_snapshot_has_no_secrets(document)
        log_event(logger, "control_plane.backup.created", outcome="success")
        return document

    def restore_tenant_row(self, tenant_id: uuid.UUID, document: dict[str, object]) -> None:
        if document.get("plane") != "control":
            raise DomainError("validation_error", "Control-plane snapshot is required.")
        match = next(
            (
                row
                for row in document.get("tenants") or []
                if isinstance(row, dict) and row.get("tenant_id") == str(tenant_id)
            ),
            None,
        )
        if match is None:
            raise DomainError("not_found", "Tenant is not in this snapshot.", http_status=404)
        current = self._tenants.get(tenant_id)
        if current is None:
            raise tenant_unavailable()
        self._tenants.update(
            current.with_agency(display_name=str(match.get("display_name") or current.display_name))
        )
        log_event(
            logger,
            "control_plane.restore.applied",
            outcome="success",
            tenant_id=str(tenant_id),
        )
