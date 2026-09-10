from __future__ import annotations

import logging
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.application.ports import TenantDatabaseRepository, TenantRepository
from control_plane.tenancy.domain.policies import (
    assert_database_is_routable,
    assert_same_tenant_binding,
    assert_tenant_is_routable,
    resolve_route_tenant_id,
    tenant_unavailable,
)
from shared_kernel.logging import log_event
from tenant.runtime.ports import (
    TenantConnection,
    TenantPool,
    target_from_record,
)

logger = logging.getLogger("vokit.tenancy")


class TenantRouter:
    def __init__(
        self,
        tenants: TenantRepository,
        databases: TenantDatabaseRepository,
        pool: TenantPool,
    ) -> None:
        self._tenants = tenants
        self._databases = databases
        self._pool = pool

    def resolve_tenant_id(
        self,
        *,
        principal_type: PrincipalType,
        membership_tenant_id: uuid.UUID | None,
        claimed_tenant_id: uuid.UUID | None,
        permissions: frozenset[str],
    ) -> uuid.UUID:
        return resolve_route_tenant_id(
            principal_type=principal_type,
            membership_tenant_id=membership_tenant_id,
            claimed_tenant_id=claimed_tenant_id,
            permissions=permissions,
        )

    @contextmanager
    def connection_for_tenant(self, tenant_id: uuid.UUID) -> Iterator[TenantConnection]:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            log_event(
                logger,
                "tenant.route.denied",
                severity="warning",
                outcome="denied",
                reason="missing_tenant",
            )
            raise tenant_unavailable()
        assert_tenant_is_routable(tenant.status)
        database = self._databases.get_for_tenant(tenant_id)
        if database is None:
            log_event(
                logger,
                "tenant.route.denied",
                severity="warning",
                outcome="denied",
                tenant_id=str(tenant_id),
                reason="missing_mapping",
            )
            raise tenant_unavailable()
        assert_database_is_routable(database.status)
        target = target_from_record(database)
        connection = self._pool.acquire(target)
        try:
            assert_same_tenant_binding(tenant_id, connection.tenant_id)
            log_event(
                logger,
                "tenant.route.success",
                outcome="success",
                tenant_id=str(tenant_id),
                database_id=str(database.id),
            )
            yield connection
        finally:
            self._pool.release(connection)
