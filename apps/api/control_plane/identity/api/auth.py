"""Authentication context and centralised permission helpers (ADR-007)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from rest_framework.request import Request

from control_plane.identity.application.ports import MembershipRecord, UserRecord
from control_plane.identity.domain.types import MembershipStatus, PrincipalType, UserStatus
from control_plane.identity.infrastructure.container import memberships, users
from shared_kernel.errors import DomainError


@dataclass(frozen=True, slots=True)
class AuthContext:
    user: UserRecord
    membership: MembershipRecord

    @property
    def is_super_admin(self) -> bool:
        return (
            self.membership.principal_type is PrincipalType.PLATFORM
            and self.membership.role == "super_admin"
        )

    @property
    def permissions(self) -> frozenset[str]:
        """DB-backed permission codes. super_admin returns empty (bypass in require_*)."""
        if self.is_super_admin:
            return frozenset()
        if self.membership.role_id is not None:
            from control_plane.identity.models import RolePermission

            return frozenset(
                RolePermission.objects.filter(role_id=self.membership.role_id).values_list(
                    "permission__code", flat=True
                )
            )
        from control_plane.identity.domain.roles import permissions_for_role

        try:
            return permissions_for_role(self.membership.role)
        except DomainError:
            return frozenset()


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


def require_platform_perm(request: Request, perm: str) -> AuthContext:
    context = require_principal(request, PrincipalType.PLATFORM)
    if context.is_super_admin:
        return context
    if perm not in context.permissions:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def require_agency_perm(request: Request, perm: str) -> AuthContext:
    context = require_principal(request, PrincipalType.AGENCY)
    if context.membership.tenant_id is None:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    if perm not in context.permissions:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def require_customer_perm(request: Request, perm: str) -> AuthContext:
    context = require_principal(request, PrincipalType.CUSTOMER)
    if context.membership.customer_id is None:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    if perm not in context.permissions:
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
    ctx = AuthContext(user=user, membership=membership)
    is_sa = ctx.is_super_admin
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
        "role": {
            "id": str(membership.role_id) if membership.role_id else None,
            "slug": membership.role,
            "namespace": membership.principal_type.value,
        },
        "permissions": [] if is_sa else sorted(ctx.permissions),
        "is_super_admin": is_sa,
    }
