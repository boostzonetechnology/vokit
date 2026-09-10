from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.customers.application.ports import (
    BanIndex,
    CustomerIndexRecord,
    CustomerIndexRepository,
)
from control_plane.customers.domain.policies import (
    BanKey,
    assert_customer_stays_on_tenant,
    ineligible_customer,
    reassignment_forbidden,
)
from control_plane.customers.domain.types import CustomerStatus
from control_plane.identity.application.invite_user import InviteUser, InviteUserCommand
from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.policies import MembershipBinding
from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.application.ports import Clock, TenantRepository
from control_plane.tenancy.domain.lifecycle import assert_agency_may_create_customer
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.lifecycle.domain import TenantCustomer
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.customers")


@dataclass(frozen=True, slots=True)
class CreateCustomerCommand:
    display_name: str
    agency_tenant_id: uuid.UUID
    actor: MembershipRecord
    privileged: bool
    owner_email: str = ""
    customer_id: uuid.UUID | None = None
    ban_keys: tuple[BanKey, ...] = ()


@dataclass(frozen=True, slots=True)
class CreatedCustomer:
    customer: TenantCustomer
    invitation_token: str | None


class CreateCustomer:
    def __init__(
        self,
        tenants: TenantRepository,
        index: CustomerIndexRepository,
        bans: BanIndex,
        lifecycle: TenantLifecycleService,
        invites: InviteUser,
        clock: Clock,
    ) -> None:
        self._tenants = tenants
        self._index = index
        self._bans = bans
        self._lifecycle = lifecycle
        self._invites = invites
        self._clock = clock

    def execute(self, command: CreateCustomerCommand) -> CreatedCustomer:
        name = command.display_name.strip()
        if not name:
            raise DomainError("validation_error", "display_name is required.")
        tenant = self._tenants.get(command.agency_tenant_id)
        if tenant is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        assert_agency_may_create_customer(
            tenant.agency_status,
            tenant.capabilities,
            privileged=command.privileged,
        )
        keys = list(command.ban_keys)
        owner_email = command.owner_email.strip()
        if owner_email:
            keys.append(BanKey(kind="email", value=owner_email))
        if self._bans.is_banned(keys):
            raise ineligible_customer()
        customer_id = command.customer_id or new_uuid7()
        existing = self._index.get(customer_id)
        if existing is not None:
            raise reassignment_forbidden()
        now = self._clock.now()
        row = TenantCustomer(
            customer_id=customer_id,
            tenant_id=tenant.id,
            display_name=name,
            status=CustomerStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        stored = self._lifecycle.put_customer(tenant.id, row)
        self._index.create(
            CustomerIndexRecord(
                id=customer_id,
                tenant_id=tenant.id,
                display_name=name,
                status=CustomerStatus.ACTIVE,
                created_at=now,
            )
        )
        token = self._invite_owner(command, tenant.id, customer_id)
        log_event(
            logger,
            "customer.created",
            outcome="success",
            tenant_id=str(tenant.id),
            customer_id=str(customer_id),
        )
        assert_customer_stays_on_tenant(
            indexed_tenant_id=tenant.id,
            route_tenant_id=stored.tenant_id,
        )
        return CreatedCustomer(customer=stored, invitation_token=token)

    def _invite_owner(
        self,
        command: CreateCustomerCommand,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> str | None:
        email = command.owner_email.strip()
        if not email:
            return None
        try:
            _record, token = self._invites.execute(
                InviteUserCommand(
                    email=email,
                    binding=MembershipBinding(
                        principal_type=PrincipalType.CUSTOMER,
                        role="customer_owner",
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                    ),
                    invited_by_id=command.actor.user_id,
                    actor_membership=command.actor,
                )
            )
            return token
        except DomainError as exc:
            if exc.code == "membership_conflict":
                return None
            raise
