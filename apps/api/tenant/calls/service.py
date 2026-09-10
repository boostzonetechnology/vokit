from __future__ import annotations

import uuid

from shared_kernel.errors import DomainError
from tenant.calls.domain import TenantCallEventRecord, TenantCallRecord
from tenant.calls.ports import TenantCallStore
from tenant.runtime.router import TenantRouter


class TenantCallService:
    def __init__(self, router: TenantRouter, store: TenantCallStore) -> None:
        self._router = router
        self._store = store

    def put_call(self, tenant_id: uuid.UUID, row: TenantCallRecord) -> TenantCallRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_call(connection, row)
            stored = self._store.get_call(connection, row.call_id)
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def get_call(self, tenant_id: uuid.UUID, call_id: uuid.UUID) -> TenantCallRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_call(connection, call_id)

    def get_by_edge(self, tenant_id: uuid.UUID, edge_call_id: str) -> TenantCallRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_call_by_edge(connection, edge_call_id)

    def put_event(self, tenant_id: uuid.UUID, row: TenantCallEventRecord) -> None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_call_event(connection, row)

    def list_calls(
        self,
        tenant_id: uuid.UUID,
        *,
        customer_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
    ) -> list[TenantCallRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_calls(
                connection, customer_id=customer_id, agent_id=agent_id
            )
