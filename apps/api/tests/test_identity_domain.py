from __future__ import annotations

import uuid

import pytest

from control_plane.identity.domain.policies import (
    MembershipBinding,
    assert_can_hold_new_membership,
    assert_privileged_mfa,
    normalize_email,
    validate_membership_binding,
)
from control_plane.identity.domain.roles import (
    AGENCY_PERMISSIONS,
    PLATFORM_PERMISSIONS,
    permissions_for_role,
)
from control_plane.identity.domain.types import PrincipalType
from shared_kernel.errors import DomainError


def test_email_is_normalized_and_unique_shape() -> None:
    assert normalize_email("  Owner@Vokit.Test ") == "owner@vokit.test"
    with pytest.raises(DomainError) as exc:
        normalize_email("not-an-email")
    assert exc.value.code == "validation_error"


def test_one_membership_xor() -> None:
    with pytest.raises(DomainError) as exc:
        assert_can_hold_new_membership(has_platform=True, has_tenant=False)
    assert exc.value.code == "membership_conflict"
    with pytest.raises(DomainError):
        assert_can_hold_new_membership(has_platform=False, has_tenant=True)
    assert_can_hold_new_membership(has_platform=False, has_tenant=False)


@pytest.mark.django_db
def test_platform_membership_cannot_carry_tenant() -> None:
    with pytest.raises(DomainError) as exc:
        validate_membership_binding(
            MembershipBinding(
                principal_type=PrincipalType.PLATFORM,
                role="super_admin",
                tenant_id=uuid.uuid4(),
                customer_id=None,
            )
        )
    assert exc.value.code == "invalid_membership"


def test_privileged_mfa_fails_closed_when_required() -> None:
    assert_privileged_mfa(role="super_admin", required=False, enrolled=False)
    assert_privileged_mfa(role="customer_owner", required=True, enrolled=False)
    with pytest.raises(DomainError) as exc:
        assert_privileged_mfa(role="finance_admin", required=True, enrolled=False)
    assert exc.value.code == "mfa_required"
    assert_privileged_mfa(role="agency_owner", required=True, enrolled=True)


@pytest.mark.django_db
def test_agency_role_cannot_use_platform_permissions() -> None:
    # ADR-007: some codes (agent.view, call.view …) exist in both platform and agency
    # namespaces — same action, different scope. Check that agency_owner permissions
    # are a subset of the agency catalog and disjoint from platform-ONLY codes.
    perms = permissions_for_role("agency_owner")
    platform_only = PLATFORM_PERMISSIONS - AGENCY_PERMISSIONS
    assert perms.isdisjoint(platform_only), (
        f"agency_owner has platform-only codes: {perms & platform_only}"
    )
    assert perms <= AGENCY_PERMISSIONS, (
        f"agency_owner has codes outside agency catalog: {perms - AGENCY_PERMISSIONS}"
    )
    with pytest.raises(DomainError) as exc:
        validate_membership_binding(
            MembershipBinding(
                principal_type=PrincipalType.AGENCY,
                role="super_admin",
                tenant_id=uuid.uuid4(),
                customer_id=None,
            )
        )
    assert exc.value.code == "invalid_role"
