from __future__ import annotations

from control_plane.audit.infrastructure.container import record_audit
from control_plane.customers.application.change_customer import ChangeCustomerStatus
from control_plane.customers.application.create_customer import CreateCustomer
from control_plane.customers.infrastructure.repositories import (
    DjangoBanIndex,
    DjangoCustomerIndexRepository,
)
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.identity.infrastructure.container import invite_user
from control_plane.tenancy.infrastructure.container import lifecycle, tenant_repo


def customer_index() -> DjangoCustomerIndexRepository:
    return DjangoCustomerIndexRepository()


def ban_index() -> DjangoBanIndex:
    return DjangoBanIndex()


def create_customer() -> CreateCustomer:
    return CreateCustomer(
        tenant_repo(),
        customer_index(),
        ban_index(),
        lifecycle(),
        invite_user(),
        SystemClock(),
    )


def change_customer_status() -> ChangeCustomerStatus:
    return ChangeCustomerStatus(
        tenant_repo(),
        customer_index(),
        lifecycle(),
        SystemClock(),
        record_audit(),
    )
