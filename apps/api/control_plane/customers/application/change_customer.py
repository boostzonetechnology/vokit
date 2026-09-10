from __future__ import annotations

import logging
import uuid

from control_plane.customers.application.ports import (
    CustomerIndexRecord,
    CustomerIndexRepository,
)
from control_plane.customers.domain.policies import customer_not_found
from control_plane.customers.domain.types import apply_customer_status_action
from control_plane.tenancy.application.ports import Clock, TenantRepository
from control_plane.tenancy.domain.lifecycle import assert_agency_may_mutate_customer
from shared_kernel.logging import log_event
from tenant.lifecycle.domain import TenantCustomer
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.customers")


class ChangeCustomerStatus:
    def __init__(
        self,
        tenants: TenantRepository,
        index: CustomerIndexRepository,
        lifecycle: TenantLifecycleService,
        clock: Clock,
    ) -> None:
        self._tenants = tenants
        self._index = index
        self._lifecycle = lifecycle
        self._clock = clock

    def execute(
        self,
        *,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        action: str,
        privileged: bool,
    ) -> TenantCustomer:
        indexed = self._index.get(customer_id)
        if indexed is None or indexed.tenant_id != tenant_id:
            raise customer_not_found()
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise customer_not_found()
        assert_agency_may_mutate_customer(
            tenant.agency_status,
            tenant.capabilities,
            privileged=privileged,
        )
        current = self._lifecycle.get_customer(tenant_id, customer_id)
        if current is None:
            raise customer_not_found()
        nxt = apply_customer_status_action(
            current.status, action, privileged=privileged
        )
        updated = TenantCustomer(
            customer_id=current.customer_id,
            tenant_id=current.tenant_id,
            display_name=current.display_name,
            status=nxt,
            created_at=current.created_at,
            updated_at=self._clock.now(),
        )
        stored = self._lifecycle.put_customer(tenant_id, updated)
        self._index.update(
            CustomerIndexRecord(
                id=indexed.id,
                tenant_id=indexed.tenant_id,
                display_name=indexed.display_name,
                status=nxt,
                created_at=indexed.created_at,
            )
        )
        log_event(
            logger,
            "customer.status.changed",
            outcome="success",
            tenant_id=str(tenant_id),
            customer_id=str(customer_id),
            status=nxt.value,
        )
        return stored
