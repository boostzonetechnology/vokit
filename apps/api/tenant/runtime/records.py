from __future__ import annotations

import uuid

from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.domain.policies import resolve_route_tenant_id
from shared_kernel.errors import DomainError
from tenant.runtime.domain import IsolationRecord, JobContext
from tenant.runtime.ports import IsolationRecordRepository
from tenant.runtime.router import TenantRouter


class IsolationRecordService:
    def __init__(self, router: TenantRouter, records: IsolationRecordRepository) -> None:
        self._router = router
        self._records = records

    def put(
        self,
        *,
        principal_type: PrincipalType,
        membership_tenant_id: uuid.UUID | None,
        claimed_tenant_id: uuid.UUID | None,
        permissions: frozenset[str],
        object_id: uuid.UUID,
        payload: str,
    ) -> IsolationRecord:
        tenant_id = resolve_route_tenant_id(
            principal_type=principal_type,
            membership_tenant_id=membership_tenant_id,
            claimed_tenant_id=claimed_tenant_id,
            permissions=permissions,
        )
        record = IsolationRecord(object_id=object_id, tenant_id=tenant_id, payload=payload)
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._records.upsert(connection, record)
            stored = self._records.get(connection, object_id)
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def get(
        self,
        *,
        principal_type: PrincipalType,
        membership_tenant_id: uuid.UUID | None,
        claimed_tenant_id: uuid.UUID | None,
        permissions: frozenset[str],
        object_id: uuid.UUID,
    ) -> IsolationRecord:
        tenant_id = resolve_route_tenant_id(
            principal_type=principal_type,
            membership_tenant_id=membership_tenant_id,
            claimed_tenant_id=claimed_tenant_id,
            permissions=permissions,
        )
        with self._router.connection_for_tenant(tenant_id) as connection:
            record = self._records.get(connection, object_id)
        if record is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return record

    def get_for_job(self, context: JobContext, object_id: uuid.UUID) -> IsolationRecord:
        if context.tenant_id is None:
            raise DomainError("tenant_route_denied", "Tenant context is missing.", http_status=403)
        with self._router.connection_for_tenant(context.tenant_id) as connection:
            record = self._records.get(connection, object_id)
        if record is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return record
