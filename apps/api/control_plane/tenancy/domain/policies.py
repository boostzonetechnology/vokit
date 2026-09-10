from __future__ import annotations

import uuid

from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.domain.types import (
    ROUTABLE_DATABASE_STATUSES,
    ROUTABLE_TENANT_STATUSES,
    DatabaseStatus,
    TenantStatus,
)
from shared_kernel.errors import DomainError


def resolve_route_tenant_id(
    *,
    principal_type: PrincipalType,
    membership_tenant_id: uuid.UUID | None,
    claimed_tenant_id: uuid.UUID | None,
    permissions: frozenset[str],
) -> uuid.UUID:
    """Browser claims never select a database. Session or privileged platform only."""
    if principal_type in {PrincipalType.AGENCY, PrincipalType.CUSTOMER}:
        if membership_tenant_id is None:
            raise DomainError(
                "tenant_route_denied",
                "Tenant context is missing.",
                http_status=403,
            )
        return membership_tenant_id
    if principal_type is PrincipalType.PLATFORM:
        if "tenants.route" not in permissions:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        if claimed_tenant_id is None:
            raise DomainError("validation_error", "tenant_id is required for platform routing.")
        return claimed_tenant_id
    raise DomainError("tenant_route_denied", "Tenant context is missing.", http_status=403)


def tenant_unavailable() -> DomainError:
    return DomainError(
        "tenant_route_denied",
        "Tenant database is not available.",
        http_status=503,
    )


def isolation_violation() -> DomainError:
    return DomainError(
        "tenant_isolation_violation",
        "Tenant context mismatch.",
        http_status=500,
    )


def db_unavailable() -> DomainError:
    return DomainError(
        "tenant_db_unavailable",
        "Tenant database is not available.",
        http_status=503,
    )


def pool_exhausted() -> DomainError:
    return DomainError(
        "tenant_pool_exhausted",
        "Tenant connection limit reached.",
        http_status=503,
    )


def assert_tenant_is_routable(status: TenantStatus) -> None:
    if status not in ROUTABLE_TENANT_STATUSES:
        raise tenant_unavailable()


def assert_database_is_routable(status: DatabaseStatus) -> None:
    if status not in ROUTABLE_DATABASE_STATUSES:
        raise tenant_unavailable()


def assert_same_tenant_binding(expected: uuid.UUID, actual: uuid.UUID) -> None:
    if expected != actual:
        raise isolation_violation()
