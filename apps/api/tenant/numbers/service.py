from __future__ import annotations

import uuid

from shared_kernel.errors import DomainError
from tenant.numbers.domain import NumberAssignmentRecord
from tenant.numbers.ports import TenantNumberStore
from tenant.runtime.router import TenantRouter


class TenantNumberService:
    def __init__(self, router: TenantRouter, store: TenantNumberStore) -> None:
        self._router = router
        self._store = store

    def put_assignment(
        self, tenant_id: uuid.UUID, row: NumberAssignmentRecord
    ) -> NumberAssignmentRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_assignment(connection, row)
            stored = self._store.get_assignment(connection, row.assignment_id)
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def get_assignment(
        self, tenant_id: uuid.UUID, assignment_id: uuid.UUID
    ) -> NumberAssignmentRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_assignment(connection, assignment_id)

    def active_for_number(
        self, tenant_id: uuid.UUID, phone_number_id: uuid.UUID
    ) -> NumberAssignmentRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.active_for_number(connection, phone_number_id)

    def list_assignments(
        self,
        tenant_id: uuid.UUID,
        *,
        customer_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
    ) -> list[NumberAssignmentRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_assignments(
                connection, customer_id=customer_id, agent_id=agent_id
            )
