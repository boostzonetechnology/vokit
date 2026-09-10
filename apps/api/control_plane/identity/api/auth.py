from __future__ import annotations

import uuid
from dataclasses import dataclass

from rest_framework.request import Request

from control_plane.identity.application.ports import MembershipRecord, UserRecord
from control_plane.identity.domain.roles import permissions_for_role
from control_plane.identity.domain.types import MembershipStatus, PrincipalType, UserStatus
from control_plane.identity.infrastructure.container import memberships, users
from shared_kernel.errors import DomainError


@dataclass(frozen=True, slots=True)
class AuthContext:
    user: UserRecord
    membership: MembershipRecord

    @property
    def permissions(self) -> frozenset[str]:
        return permissions_for_role(self.membership.role)


def django_user(request: Request):
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        raw = getattr(request, "_request", request)
        user = getattr(raw, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        raise DomainError("unauthenticated", "Authentication required.", http_status=401)
    return user


def require_auth(request: Request) -> AuthContext:
    current = django_user(request)
    user = users().get_by_id(current.id)
    membership = memberships().get_for_user(current.id)
    if (
        user is None
        or membership is None
        or user.status is not UserStatus.ACTIVE
        or membership.status is not MembershipStatus.ACTIVE
    ):
        raise DomainError("unauthenticated", "Authentication required.", http_status=401)
    return AuthContext(user=user, membership=membership)


def require_principal(request: Request, principal_type: PrincipalType) -> AuthContext:
    context = require_auth(request)
    if context.membership.principal_type is not principal_type:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def parse_uuid(value: object, *, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise DomainError("validation_error", f"{field} is invalid.") from exc


def parse_optional_uuid(value: object, *, field: str) -> uuid.UUID | None:
    if value in (None, ""):
        return None
    return parse_uuid(value, field=field)


def session_payload(user: UserRecord, membership: MembershipRecord) -> dict[str, object]:
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "status": user.status.value,
        },
        "membership": {
            "id": str(membership.id),
            "principal_type": membership.principal_type.value,
            "role": membership.role,
            "tenant_id": str(membership.tenant_id) if membership.tenant_id else None,
            "customer_id": str(membership.customer_id) if membership.customer_id else None,
            "status": membership.status.value,
        },
        "permissions": sorted(permissions_for_role(membership.role)),
    }
