from __future__ import annotations

import uuid
from typing import Protocol

from tenant.lifecycle.domain import AgencyProfile, TenantCustomer
from tenant.runtime.ports import TenantConnection


class TenantLifecycleStore(Protocol):
    def put_agency(self, connection: TenantConnection, profile: AgencyProfile) -> None: ...

    def get_agency(self, connection: TenantConnection) -> AgencyProfile | None: ...

    def put_customer(self, connection: TenantConnection, customer: TenantCustomer) -> None: ...

    def get_customer(
        self, connection: TenantConnection, customer_id: uuid.UUID
    ) -> TenantCustomer | None: ...

    def list_customers(self, connection: TenantConnection) -> list[TenantCustomer]: ...
