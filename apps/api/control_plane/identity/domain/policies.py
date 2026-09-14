from __future__ import annotations

import uuid
from dataclasses import dataclass

from control_plane.identity.domain.roles import assert_role_matches_principal
from control_plane.identity.domain.types import PrincipalType, UserStatus
from shared_kernel.errors import DomainError


def normalize_email(email: str) -> str:
    value = (email or "").strip().lower()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise DomainError("validation_error", "A valid email is required.")
    return value


@dataclass(frozen=True, slots=True)
class MembershipBinding:
    principal_type: PrincipalType
    role: str
    tenant_id: uuid.UUID | None
    customer_id: uuid.UUID | None


def validate_membership_binding(binding: MembershipBinding) -> None:
    """Validate role namespace and scope constraints.

    ADR-007: assert_role_matches_principal now queries the DB Role record
    (with static-set fallback for offline unit tests).
    """
    assert_role_matches_principal(binding.role, binding.principal_type)
    if binding.principal_type is PrincipalType.PLATFORM:
        if binding.tenant_id is not None or binding.customer_id is not None:
            raise DomainError("invalid_membership", "Platform users are not tenant members.")
        return
    if binding.tenant_id is None:
        raise DomainError("invalid_membership", "Tenant membership requires a tenant.")
    if binding.principal_type is PrincipalType.AGENCY and binding.customer_id is not None:
        raise DomainError("invalid_membership", "Agency membership cannot include a customer.")
    if binding.principal_type is PrincipalType.CUSTOMER and binding.customer_id is None:
        raise DomainError("invalid_membership", "Customer membership requires a customer.")


PRIVILEGED_MFA_ROLES = frozenset(
    {"super_admin", "finance_admin", "compliance_kyc", "agency_owner"}
)


def assert_user_can_authenticate(status: UserStatus) -> None:
    if status is not UserStatus.ACTIVE:
        raise DomainError("unauthenticated", "Invalid email or password.", http_status=401)


def assert_privileged_mfa(*, role: str, required: bool, enrolled: bool) -> None:
    if required and role in PRIVILEGED_MFA_ROLES and not enrolled:
        raise DomainError(
            "mfa_required",
            "MFA is required for this role.",
            http_status=403,
        )


def assert_can_hold_new_membership(*, has_platform: bool, has_tenant: bool) -> None:
    if has_platform or has_tenant:
        raise DomainError(
            "membership_conflict",
            "A user can belong to only one platform or tenant context.",
            http_status=409,
        )
