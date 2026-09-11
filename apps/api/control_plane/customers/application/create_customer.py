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
from control_plane.notifications.application.hooks import deliver_invitation
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
    owner_email: str
    customer_id: uuid.UUID | None = None
    ban_keys: tuple[BanKey, ...] = ()
    legal_name: str = ""
    phone: str = ""
    country: str = ""
    timezone: str = ""


@dataclass(frozen=True, slots=True)
class CreatedCustomer:
    customer: TenantCustomer


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
        owner_email = command.owner_email.strip()
        if not owner_email:
            raise DomainError("validation_error", "owner_email is required.")
        tenant = self._tenants.get(command.agency_tenant_id)
        if tenant is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        assert_agency_may_create_customer(
            tenant.agency_status,
            tenant.capabilities,
            privileged=command.privileged,
        )
        keys = list(command.ban_keys)
        keys.append(BanKey(kind="email", value=owner_email))
        if self._bans.is_banned(keys):
            raise ineligible_customer()
        customer_id = command.customer_id or new_uuid7()
        existing = self._index.get(customer_id)
        if existing is not None:
            raise reassignment_forbidden()
        now = self._clock.now()
        legal_name = (command.legal_name or "").strip() or name
        row = TenantCustomer(
            customer_id=customer_id,
            tenant_id=tenant.id,
            display_name=name,
            status=CustomerStatus.INVITED,
            legal_name=legal_name,
            owner_email=owner_email,
            phone=(command.phone or "").strip(),
            country=(command.country or "").strip(),
            timezone=(command.timezone or "").strip(),
            created_at=now,
            updated_at=now,
        )
        stored = self._lifecycle.put_customer(tenant.id, row)
        self._index.create(
            CustomerIndexRecord(
                id=customer_id,
                tenant_id=tenant.id,
                display_name=name,
                status=CustomerStatus.INVITED,
                created_at=now,
            )
        )
        try:
            self._invite_owner(command, tenant.id, customer_id, owner_email)
        except DomainError:
            self._lifecycle.put_customer(
                tenant.id,
                TenantCustomer(
                    customer_id=stored.customer_id,
                    tenant_id=stored.tenant_id,
                    display_name=stored.display_name,
                    status=CustomerStatus.CLOSED,
                    legal_name=stored.legal_name,
                    owner_email=stored.owner_email,
                    phone=stored.phone,
                    country=stored.country,
                    timezone=stored.timezone,
                    created_at=stored.created_at,
                    updated_at=self._clock.now(),
                ),
            )
            self._index.update(
                CustomerIndexRecord(
                    id=customer_id,
                    tenant_id=tenant.id,
                    display_name=name,
                    status=CustomerStatus.CLOSED,
                    created_at=now,
                )
            )
            raise
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
        saved = self._lifecycle.get_customer(tenant.id, customer_id) or stored
        return CreatedCustomer(customer=saved)

    def _invite_owner(
        self,
        command: CreateCustomerCommand,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        owner_email: str,
    ) -> None:
        try:
            record, token = self._invites.execute(
                InviteUserCommand(
                    email=owner_email,
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
        except DomainError as exc:
            if exc.code == "membership_conflict":
                raise DomainError(
                    "owner_conflict",
                    "Owner email already has a membership.",
                    http_status=409,
                ) from exc
            raise
        deliver_invitation(
            email=record.email,
            role=record.role,
            principal_type=record.principal_type,
            tenant_id=record.tenant_id,
            customer_id=record.customer_id,
            token=token,
            actor_id=command.actor.user_id,
            actor_role=command.actor.role,
        )
