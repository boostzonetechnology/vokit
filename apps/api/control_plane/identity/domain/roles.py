"""
Role namespace catalogs and DB-backed permission helpers.

ADR-007: ROLE_PERMISSIONS static dict is removed. Permissions are now stored
in identity_roles / identity_role_permissions and loaded from DB at runtime.

Kept static:
  PLATFORM_ROLES, AGENCY_ROLES, CUSTOMER_ROLES  — namespace membership of
  system roles; used by namespace_for_role() with DB fallback for custom roles.

namespace_for_role()      — static lookup for system roles; DB fallback.
assert_role_matches_principal() — checks via DB Role record.
permissions_for_role(slug) — DB query; returns frozenset[str].
"""

from __future__ import annotations

from control_plane.identity.domain.permission_catalog import PERMISSION_CATALOG
from control_plane.identity.domain.types import PrincipalType
from shared_kernel.errors import DomainError

# ---------------------------------------------------------------------------
# Static namespace sets — system roles
# ---------------------------------------------------------------------------

PLATFORM_ROLES: frozenset[str] = frozenset(
    {"super_admin", "finance_admin", "compliance_kyc", "support_admin"}
)
AGENCY_ROLES: frozenset[str] = frozenset(
    {"agency_owner", "agency_admin", "agency_agent_builder", "agency_finance"}
)
CUSTOMER_ROLES: frozenset[str] = frozenset(
    {"customer_owner", "customer_admin", "customer_analyst"}
)

# ---------------------------------------------------------------------------
# Backward-compat permission code sets (derived from catalog, not static)
# Preferred for namespace-disjointness assertions and tests.
# ---------------------------------------------------------------------------

PLATFORM_PERMISSIONS: frozenset[str] = frozenset(
    s.code for s in PERMISSION_CATALOG if s.namespace == "platform"
)
AGENCY_PERMISSIONS: frozenset[str] = frozenset(
    s.code for s in PERMISSION_CATALOG if s.namespace == "agency"
)
CUSTOMER_PERMISSIONS: frozenset[str] = frozenset(
    s.code for s in PERMISSION_CATALOG if s.namespace == "customer"
)


def namespace_for_role(role: str) -> PrincipalType:
    """Return the principal namespace for a role slug.

    Uses static sets for known system roles; falls back to DB for custom roles.
    Raises DomainError("invalid_role") if the role is unknown in both sources.
    """
    if role in PLATFORM_ROLES:
        return PrincipalType.PLATFORM
    if role in AGENCY_ROLES:
        return PrincipalType.AGENCY
    if role in CUSTOMER_ROLES:
        return PrincipalType.CUSTOMER
    # DB fallback for custom roles
    from control_plane.identity.models import Role as RoleModel  # lazy import

    row = RoleModel.objects.filter(slug=role).first()
    if row is None:
        raise DomainError("invalid_role", "Unknown role.")
    return PrincipalType(row.namespace)


def assert_role_matches_principal(role: str, principal_type: PrincipalType) -> None:
    """Raise DomainError if the role does not belong to the given namespace.

    Prefers DB lookup (authoritative) with static-set fallback for offline unit tests.
    """
    from control_plane.identity.models import Role as RoleModel  # lazy import

    row = RoleModel.objects.filter(slug=role).first()
    if row is not None:
        actual = PrincipalType(row.namespace)
        if actual is not principal_type:
            raise DomainError(
                "invalid_role", "Role does not belong to this permission namespace."
            )
        return
    # Fallback: static namespace sets (used when RBAC tables not yet seeded)
    if namespace_for_role(role) is not principal_type:
        raise DomainError("invalid_role", "Role does not belong to this permission namespace.")


def permissions_for_role(slug: str) -> frozenset[str]:
    """Load the effective permission code set for a role slug from DB.

    Returns an empty frozenset for super_admin (bypass, no pivot rows).
    Raises DomainError("invalid_role") if the role slug is not found.
    """
    from control_plane.identity.models import (  # lazy imports
        Role as RoleModel,
    )
    from control_plane.identity.models import (
        RolePermission as RolePermissionModel,
    )

    role_row = RoleModel.objects.filter(slug=slug).first()
    if role_row is None:
        raise DomainError("invalid_role", f"Unknown role: {slug!r}.")

    codes = (
        RolePermissionModel.objects.filter(role_id=role_row.id)
        .select_related("permission")
        .values_list("permission__code", flat=True)
    )
    return frozenset(codes)
