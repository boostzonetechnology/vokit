from __future__ import annotations

import uuid

from control_plane.identity.application.ports import (
    InvitationRecord,
    MembershipRecord,
    UserRecord,
)
from control_plane.identity.domain.types import (
    InvitationStatus,
    MembershipStatus,
    PrincipalType,
    UserStatus,
)
from control_plane.identity.models import Invitation, Membership, User
from shared_kernel.errors import DomainError


def _user_record(row: User) -> UserRecord:
    return UserRecord(
        id=row.id,
        email=row.email,
        password_hash=row.password,
        status=UserStatus(row.status),
    )


def _membership_record(row: Membership) -> MembershipRecord:
    return MembershipRecord(
        id=row.id,
        user_id=row.user_id,
        principal_type=PrincipalType(row.principal_type),
        role=row.role,
        tenant_id=row.tenant_id,
        customer_id=row.customer_id,
        status=MembershipStatus(row.status),
    )


class DjangoUserRepository:
    def get_by_email(self, email: str) -> UserRecord | None:
        row = User.objects.filter(email=email).first()
        return _user_record(row) if row else None

    def get_by_id(self, user_id: uuid.UUID) -> UserRecord | None:
        row = User.objects.filter(id=user_id).first()
        return _user_record(row) if row else None

    def list_by_ids(self, user_ids: list[uuid.UUID]) -> list[UserRecord]:
        rows = User.objects.filter(id__in=user_ids)
        return [_user_record(row) for row in rows]

    def create(self, user: UserRecord) -> None:
        User.objects.create(
            id=user.id,
            email=user.email,
            password=user.password_hash,
            status=user.status.value,
        )

    def update_status(self, user_id: uuid.UUID, status: UserStatus) -> None:
        User.objects.filter(id=user_id).update(status=status.value)


class DjangoMembershipRepository:
    def get_for_user(self, user_id: uuid.UUID) -> MembershipRecord | None:
        row = Membership.objects.filter(user_id=user_id).first()
        return _membership_record(row) if row else None

    def has_platform(self, user_id: uuid.UUID) -> bool:
        return Membership.objects.filter(user_id=user_id, principal_type="platform").exists()

    def has_tenant(self, user_id: uuid.UUID) -> bool:
        return Membership.objects.filter(
            user_id=user_id, principal_type__in=["agency", "customer"]
        ).exists()

    def create(self, membership: MembershipRecord) -> None:
        if Membership.objects.filter(user_id=membership.user_id).exists():
            raise DomainError(
                "membership_conflict",
                "A user can belong to only one platform or tenant context.",
                http_status=409,
            )
        Membership.objects.create(
            id=membership.id,
            user_id=membership.user_id,
            principal_type=membership.principal_type.value,
            role=membership.role,
            tenant_id=membership.tenant_id,
            customer_id=membership.customer_id,
            status=membership.status.value,
        )

    def list_for_scope(
        self,
        *,
        principal_type: PrincipalType,
        tenant_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
    ) -> list[MembershipRecord]:
        if principal_type is PrincipalType.PLATFORM:
            rows = Membership.objects.filter(principal_type="platform")
            return [_membership_record(row) for row in rows]
        query = Membership.objects.filter(principal_type=principal_type.value, tenant_id=tenant_id)
        if principal_type is PrincipalType.CUSTOMER:
            query = query.filter(customer_id=customer_id)
        return [_membership_record(row) for row in query]

    def update_status(self, membership_id: uuid.UUID, status: MembershipStatus) -> None:
        Membership.objects.filter(id=membership_id).update(status=status.value)


class DjangoInvitationRepository:
    def get_by_token_hash(self, token_hash: str) -> InvitationRecord | None:
        row = Invitation.objects.filter(token_hash=token_hash).first()
        return self._to_record(row) if row else None

    def create(self, invitation: InvitationRecord) -> None:
        Invitation.objects.create(
            id=invitation.id,
            email=invitation.email,
            principal_type=invitation.principal_type.value,
            role=invitation.role,
            tenant_id=invitation.tenant_id,
            customer_id=invitation.customer_id,
            token_hash=invitation.token_hash,
            status=invitation.status.value,
            expires_at=invitation.expires_at,
            invited_by_id=invitation.invited_by_id,
        )

    def mark_accepted(self, invitation_id: uuid.UUID) -> None:
        Invitation.objects.filter(id=invitation_id).update(status=InvitationStatus.ACCEPTED.value)

    def list_open_for_email(self, email: str) -> list[InvitationRecord]:
        rows = Invitation.objects.filter(email=email, status=InvitationStatus.INVITED.value)
        return [self._to_record(row) for row in rows]

    def list_for_scope(
        self,
        *,
        principal_type: PrincipalType,
        tenant_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
    ) -> list[InvitationRecord]:
        query = Invitation.objects.all().order_by("-created_at")
        if principal_type is PrincipalType.PLATFORM:
            return [self._to_record(row) for row in query]
        query = query.filter(tenant_id=tenant_id)
        if principal_type is PrincipalType.CUSTOMER:
            query = query.filter(customer_id=customer_id)
        return [self._to_record(row) for row in query]

    def _to_record(self, row: Invitation) -> InvitationRecord:
        return InvitationRecord(
            id=row.id,
            email=row.email,
            principal_type=PrincipalType(row.principal_type),
            role=row.role,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            token_hash=row.token_hash,
            status=InvitationStatus(row.status),
            expires_at=row.expires_at,
            invited_by_id=row.invited_by_id,
        )
