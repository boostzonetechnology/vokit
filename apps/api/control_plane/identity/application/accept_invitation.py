from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from control_plane.identity.application.ports import (
    Clock,
    InvitationRepository,
    MembershipRecord,
    MembershipRepository,
    PasswordHasher,
    UserRecord,
    UserRepository,
)
from control_plane.identity.domain.policies import (
    MembershipBinding,
    assert_can_hold_new_membership,
    normalize_email,
    validate_membership_binding,
)
from control_plane.identity.domain.tokens import hash_invitation_token
from control_plane.identity.domain.types import (
    InvitationStatus,
    MembershipStatus,
    PrincipalType,
    UserStatus,
)
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7


class CustomerInviteActivator(Protocol):
    def execute(self, *, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> None: ...


@dataclass(frozen=True, slots=True)
class AcceptInvitationCommand:
    token: str
    password: str


class AcceptInvitation:
    def __init__(
        self,
        users: UserRepository,
        memberships: MembershipRepository,
        invitations: InvitationRepository,
        passwords: PasswordHasher,
        clock: Clock,
        activate_customer: CustomerInviteActivator | None = None,
    ) -> None:
        self._users = users
        self._memberships = memberships
        self._invitations = invitations
        self._passwords = passwords
        self._clock = clock
        self._activate_customer = activate_customer

    def execute(self, command: AcceptInvitationCommand) -> UserRecord:
        invitation = self._invitations.get_by_token_hash(hash_invitation_token(command.token))
        if invitation is None or invitation.status is not InvitationStatus.INVITED:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if invitation.expires_at <= self._clock.now():
            raise DomainError("not_found", "Resource not found.", http_status=404)
        binding = MembershipBinding(
            principal_type=invitation.principal_type,
            role=invitation.role,
            tenant_id=invitation.tenant_id,
            customer_id=invitation.customer_id,
        )
        validate_membership_binding(binding)
        email = normalize_email(invitation.email)
        user = self._users.get_by_email(email)
        if user is None:
            if len(command.password) < 12:
                raise DomainError("validation_error", "Password must be at least 12 characters.")
            user = UserRecord(
                id=new_uuid7(),
                email=email,
                password_hash=self._passwords.hash(command.password),
                status=UserStatus.ACTIVE,
            )
            self._users.create(user)
        else:
            if user.status is UserStatus.DISABLED:
                raise DomainError("unauthenticated", "Invalid email or password.", http_status=401)
            assert_can_hold_new_membership(
                has_platform=self._memberships.has_platform(user.id),
                has_tenant=self._memberships.has_tenant(user.id),
            )
            if not self._passwords.verify(command.password, user.password_hash):
                raise DomainError("unauthenticated", "Invalid email or password.", http_status=401)
        self._memberships.create(
            MembershipRecord(
                id=new_uuid7(),
                user_id=user.id,
                principal_type=invitation.principal_type,
                role=invitation.role,
                tenant_id=invitation.tenant_id,
                customer_id=invitation.customer_id,
                status=MembershipStatus.ACTIVE,
            )
        )
        self._invitations.mark_accepted(invitation.id)
        if (
            self._activate_customer is not None
            and invitation.principal_type is PrincipalType.CUSTOMER
            and invitation.tenant_id is not None
            and invitation.customer_id is not None
        ):
            self._activate_customer.execute(
                tenant_id=invitation.tenant_id,
                customer_id=invitation.customer_id,
            )
        return user
