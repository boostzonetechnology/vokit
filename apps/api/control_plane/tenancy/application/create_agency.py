from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.identity.application.invite_user import InviteUser, InviteUserCommand
from control_plane.identity.application.ports import MembershipRecord
from control_plane.identity.domain.policies import MembershipBinding
from control_plane.identity.domain.types import PrincipalType
from control_plane.notifications.application.hooks import deliver_invitation
from control_plane.tenancy.application.allocate_database import allocate_tenant_database
from control_plane.tenancy.application.ports import (
    Clock,
    TenantDatabaseRepository,
    TenantRecord,
    TenantRepository,
)
from control_plane.tenancy.application.provision_tenant import (
    ProvisionTenant,
    ProvisionTenantCommand,
)
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities, AgencyStatus
from control_plane.tenancy.domain.types import TenantStatus
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.lifecycle.domain import AgencyProfile
from tenant.lifecycle.service import TenantLifecycleService

logger = logging.getLogger("vokit.tenancy")


@dataclass(frozen=True, slots=True)
class CreateAgencyCommand:
    display_name: str
    legal_name: str
    owner_email: str
    actor: MembershipRecord
    db_username: str
    db_password: str
    db_host: str | None = None
    db_port: int | None = None
    commission_rate_bps: int = 0
    currency: str = "USD"
    capabilities: AgencyCapabilities = AgencyCapabilities()
    tenant_id: uuid.UUID | None = None
    # Management seeds only (e.g. TENANT_DB_NAME_A). Never accepted from HTTP.
    database_name: str | None = None


@dataclass(frozen=True, slots=True)
class CreatedAgency:
    tenant: TenantRecord


class CreateAgency:
    def __init__(
        self,
        provision: ProvisionTenant,
        tenants: TenantRepository,
        databases: TenantDatabaseRepository,
        lifecycle: TenantLifecycleService,
        invites: InviteUser,
        clock: Clock,
    ) -> None:
        self._provision = provision
        self._tenants = tenants
        self._databases = databases
        self._lifecycle = lifecycle
        self._invites = invites
        self._clock = clock

    def execute(self, command: CreateAgencyCommand) -> CreatedAgency:
        self._validate(command)
        tenant_id = command.tenant_id or new_uuid7()
        allocated = allocate_tenant_database(
            tenant_id,
            db_username=command.db_username,
            db_password=command.db_password,
            db_host=command.db_host,
            db_port=command.db_port,
            name_override=command.database_name,
        )
        tenant = self._provision.execute(
            ProvisionTenantCommand(
                display_name=command.display_name.strip(),
                host=allocated.host,
                port=allocated.port,
                name=allocated.name,
                db_username=allocated.db_username,
                db_password=allocated.db_password,
                secret_ref=allocated.secret_ref,
                tls_required=allocated.tls_required,
                tenant_id=tenant_id,
            )
        )
        if tenant.status is not TenantStatus.READY:
            raise DomainError(
                "tenant_not_ready",
                "Agency database is not ready.",
                http_status=503,
            )
        now = self._clock.now()
        updated = tenant.with_agency(
            display_name=command.display_name.strip(),
            agency_status=AgencyStatus.INVITED,
            legal_name=command.legal_name.strip() or command.display_name.strip(),
            currency=command.currency,
            commission_rate_bps=command.commission_rate_bps,
            rate_effective_at=now,
            capabilities=command.capabilities,
        )
        self._tenants.update(updated)
        self._lifecycle.put_agency(
            updated.id,
            AgencyProfile(
                tenant_id=updated.id,
                display_name=updated.display_name,
                legal_name=updated.legal_name,
                status=updated.agency_status,
                currency=updated.currency,
                capabilities=updated.capabilities,
                updated_at=now,
            ),
        )
        self._invite_owner(command, updated.id)
        log_event(
            logger,
            "agency.created",
            outcome="success",
            tenant_id=str(updated.id),
        )
        saved = self._tenants.get(updated.id) or updated
        return CreatedAgency(tenant=saved)

    def _invite_owner(self, command: CreateAgencyCommand, tenant_id: uuid.UUID) -> None:
        try:
            record, token = self._invites.execute(
                InviteUserCommand(
                    email=command.owner_email,
                    binding=MembershipBinding(
                        principal_type=PrincipalType.AGENCY,
                        role="agency_owner",
                        tenant_id=tenant_id,
                        customer_id=None,
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

    def _validate(self, command: CreateAgencyCommand) -> None:
        if not command.display_name.strip():
            raise DomainError("validation_error", "display_name is required.")
        if command.currency != "USD":
            raise DomainError("validation_error", "V1 agencies are USD only.")
        if command.commission_rate_bps < 0 or command.commission_rate_bps > 10000:
            raise DomainError("validation_error", "commission_rate_bps is invalid.")
        if not command.owner_email.strip():
            raise DomainError("validation_error", "owner_email is required.")
        username = (command.db_username or "").strip()
        if not username:
            raise DomainError("validation_error", "username is required.")
        existing = self._databases.get_by_username(username)
        if existing is not None:
            raise DomainError(
                "db_username_conflict",
                "Database username is already in use.",
                http_status=409,
            )
