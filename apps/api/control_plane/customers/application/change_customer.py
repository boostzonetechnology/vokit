from __future__ import annotations

import logging
import uuid

from control_plane.audit.application.record import RecordAudit, RecordAuditCommand
from control_plane.customers.application.ports import (
    CustomerIndexRecord,
    CustomerIndexRepository,
)
from control_plane.customers.domain.policies import customer_not_found
from control_plane.customers.domain.types import CustomerStatus, apply_customer_status_action
from control_plane.tenancy.application.ports import Clock, TenantRepository
from control_plane.tenancy.domain.lifecycle import assert_agency_may_mutate_customer
from shared_kernel.errors import DomainError
from shared_kernel.logging import log_event
from tenant.lifecycle.domain import TenantCustomer
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.customers")


def _copy_customer(
    current: TenantCustomer, *, status: CustomerStatus, updated_at
) -> TenantCustomer:
    return TenantCustomer(
        customer_id=current.customer_id,
        tenant_id=current.tenant_id,
        display_name=current.display_name,
        status=status,
        legal_name=current.legal_name,
        owner_email=current.owner_email,
        phone=current.phone,
        country=current.country,
        timezone=current.timezone,
        created_at=current.created_at,
        updated_at=updated_at,
    )


class ChangeCustomerStatus:
    def __init__(
        self,
        tenants: TenantRepository,
        index: CustomerIndexRepository,
        lifecycle: TenantLifecycleService,
        clock: Clock,
        audit: RecordAudit,
    ) -> None:
        self._tenants = tenants
        self._index = index
        self._lifecycle = lifecycle
        self._clock = clock
        self._audit = audit

    def execute(
        self,
        *,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        action: str,
        privileged: bool,
        reason: str = "",
        actor_id: uuid.UUID | None = None,
        actor_role: str = "",
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
        normalized = (action or "").strip().lower()
        if normalized in {"suspend", "close"} and not reason.strip():
            raise DomainError("validation_error", "reason is required.")
        nxt = apply_customer_status_action(
            current.status, action, privileged=privileged
        )
        stored = self._lifecycle.put_customer(
            tenant_id,
            _copy_customer(current, status=nxt, updated_at=self._clock.now()),
        )
        self._index.update(
            CustomerIndexRecord(
                id=indexed.id,
                tenant_id=indexed.tenant_id,
                display_name=indexed.display_name,
                status=nxt,
                created_at=indexed.created_at,
            )
        )
        self._audit.execute(
            RecordAuditCommand(
                action="customer.status.changed",
                entity_type="customer",
                entity_id=str(customer_id),
                actor_id=actor_id,
                actor_role=actor_role,
                tenant_id=tenant_id,
                customer_id=customer_id,
                reason=reason,
                before_summary=current.status.value,
                after_summary=nxt.value,
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


class ActivateCustomerOnInviteAccept:
    """Promotes Invited → Active when a customer-owner invitation is accepted."""

    def __init__(
        self,
        index: CustomerIndexRepository,
        lifecycle: TenantLifecycleService,
        clock: Clock,
    ) -> None:
        self._index = index
        self._lifecycle = lifecycle
        self._clock = clock

    def execute(self, *, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> None:
        indexed = self._index.get(customer_id)
        if indexed is None or indexed.tenant_id != tenant_id:
            return
        current = self._lifecycle.get_customer(tenant_id, customer_id)
        if current is None or current.status is not CustomerStatus.INVITED:
            return
        self._lifecycle.put_customer(
            tenant_id,
            _copy_customer(current, status=CustomerStatus.ACTIVE, updated_at=self._clock.now()),
        )
        self._index.update(
            CustomerIndexRecord(
                id=indexed.id,
                tenant_id=indexed.tenant_id,
                display_name=indexed.display_name,
                status=CustomerStatus.ACTIVE,
                created_at=indexed.created_at,
            )
        )
