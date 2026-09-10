from __future__ import annotations

import uuid

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
    rows = list(query)
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
