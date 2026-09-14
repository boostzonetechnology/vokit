from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

from control_plane.identity.application.ports import (
    Clock,
    InvitationRecord,
    InvitationRepository,
    MembershipRecord,
    MembershipRepository,
    UserRepository,
)
from control_plane.identity.domain.policies import (
    MembershipBinding,
    normalize_email,
    validate_membership_binding,
)
from control_plane.identity.domain.roles import permissions_for_role
from control_plane.identity.domain.tokens import hash_invitation_token
from control_plane.identity.domain.types import InvitationStatus
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7


@dataclass(frozen=True, slots=True)
class InviteUserCommand:
    email: str
    binding: MembershipBinding
    invited_by_id: uuid.UUID
    actor_membership: MembershipRecord


class InviteUser:
    def __init__(
        self,
        users: UserRepository,
        memberships: MembershipRepository,
        invitations: InvitationRepository,
        clock: Clock,
        ttl: timedelta,
    ) -> None:
        self._users = users
        self._memberships = memberships
        self._invitations = invitations
        self._clock = clock
        self._ttl = ttl

    def execute(self, command: InviteUserCommand) -> tuple[InvitationRecord, str]:
        validate_membership_binding(command.binding)
        self._assert_actor_may_invite(command)
        email = normalize_email(command.email)
        existing = self._users.get_by_email(email)
        if existing is not None:
            taken = self._memberships.has_platform(existing.id) or self._memberships.has_tenant(
                existing.id
            )
            if taken:
                raise DomainError(
                    "membership_conflict",
                    "A user can belong to only one platform or tenant context.",
                    http_status=409,
                )
        token = secrets.token_urlsafe(32)
        record = InvitationRecord(
            id=new_uuid7(),
            email=email,
            principal_type=command.binding.principal_type,
            role=command.binding.role,
            # role_id resolved by DjangoInvitationRepository.create() from slug
            tenant_id=command.binding.tenant_id,
            customer_id=command.binding.customer_id,
            token_hash=hash_invitation_token(token),
            status=InvitationStatus.INVITED,
            expires_at=self._clock.now() + self._ttl,
            invited_by_id=command.invited_by_id,
        )
        self._invitations.create(record)
        return record, token

    def _assert_actor_may_invite(self, command: InviteUserCommand) -> None:
        actor = command.actor_membership
        target = command.binding
        if actor.principal_type.value == "platform":
            # super_admin bypasses all permission checks (ADR-007).
            if actor.role == "super_admin":
                return
            # ADR-007: new code for platform user invite is user.create
            perms = permissions_for_role(actor.role)
            if "user.create" not in perms:
                raise DomainError("forbidden", "Not permitted.", http_status=403)
            return
        # ADR-007: new code for team invite is team.create
        perms = permissions_for_role(actor.role)
        if "team.create" not in perms:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        if actor.tenant_id is None or actor.tenant_id != target.tenant_id:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        if actor.principal_type.value == "agency":
            if target.principal_type.value not in {"agency", "customer"}:
                raise DomainError("forbidden", "Not permitted.", http_status=403)
            return
        if actor.principal_type.value == "customer":
            if (
                target.principal_type.value != "customer"
                or target.customer_id is None
                or target.customer_id != actor.customer_id
            ):
                raise DomainError("forbidden", "Not permitted.", http_status=403)
