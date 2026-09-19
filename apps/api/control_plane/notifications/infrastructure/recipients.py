from __future__ import annotations

import uuid

from django.db.models import Q

from control_plane.identity.domain.types import MembershipStatus, PrincipalType
from control_plane.identity.models import Membership, User
from control_plane.notifications.application.ports import Recipient


def recipients_for_scope(
    *,
    tenant_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
    platform: bool = False,
) -> list[Recipient]:
    query = Membership.objects.filter(status=MembershipStatus.ACTIVE.value)
    if customer_id is not None:
        query = query.filter(
            principal_type=PrincipalType.CUSTOMER.value,
            customer_id=customer_id,
        )
    elif tenant_id is not None:
        query = query.filter(
            principal_type=PrincipalType.AGENCY.value,
            tenant_id=tenant_id,
        )
    elif platform:
        query = query.filter(principal_type=PrincipalType.PLATFORM.value)
    return _recipients_from_memberships(list(query))


def _recipients_from_memberships(rows: list[Membership]) -> list[Recipient]:
    emails = {
        row.id: row.email
        for row in User.objects.filter(id__in=[item.user_id for item in rows])
    }
    return [
        Recipient(
            user_id=row.user_id,
            email=emails.get(row.user_id, ""),
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
        )
        for row in rows
        if emails.get(row.user_id)
    ]


def recipients_for_platform_perm(code: str) -> list[Recipient]:
    query = (
        Membership.objects.filter(
            status=MembershipStatus.ACTIVE.value,
            principal_type=PrincipalType.PLATFORM.value,
        )
        .filter(
            Q(role__slug="super_admin")
            | Q(
                role__role_permissions__permission__namespace="platform",
                role__role_permissions__permission__code=code,
            )
        )
        .distinct()
    )
    return _recipients_from_memberships(list(query))


def invitation_recipient(
    *,
    email: str,
    tenant_id: uuid.UUID | None,
    customer_id: uuid.UUID | None,
) -> Recipient:
    user = User.objects.filter(email=email).first()
    return Recipient(
        user_id=user.id if user else None,
        email=email,
        tenant_id=tenant_id,
        customer_id=customer_id,
    )
