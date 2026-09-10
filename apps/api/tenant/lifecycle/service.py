from __future__ import annotations

import uuid

from tenant.lifecycle.domain import AgencyProfile, TenantCustomer
from tenant.lifecycle.ports import TenantLifecycleStore
from tenant.runtime.router import TenantRouter


class TenantLifecycleService:
    def __init__(self, router: TenantRouter, store: TenantLifecycleStore) -> None:
        self._router = router
        self._store = store

    def put_agency(self, tenant_id: uuid.UUID, profile: AgencyProfile) -> AgencyProfile:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_agency(connection, profile)
            stored = self._store.get_agency(connection)
        if stored is None:
            from shared_kernel.errors import DomainError

            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def get_agency(self, tenant_id: uuid.UUID) -> AgencyProfile | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_agency(connection)

    def put_customer(self, tenant_id: uuid.UUID, customer: TenantCustomer) -> TenantCustomer:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_customer(connection, customer)
            stored = self._store.get_customer(connection, customer.customer_id)
        if stored is None:
            from shared_kernel.errors import DomainError

            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def get_customer(
        self, tenant_id: uuid.UUID, customer_id: uuid.UUID
    ) -> TenantCustomer | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_customer(connection, customer_id)

    def list_customers(self, tenant_id: uuid.UUID) -> list[TenantCustomer]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_customers(connection)
