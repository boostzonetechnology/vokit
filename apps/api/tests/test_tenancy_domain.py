from __future__ import annotations

import uuid

import pytest

from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.domain.policies import (
    assert_tenant_is_routable,
    resolve_route_tenant_id,
)
from control_plane.tenancy.domain.types import TenantStatus
from shared_kernel.errors import DomainError

TENANT_A = uuid.UUID("0199aaaa-0000-7000-8000-000000000001")
TENANT_B = uuid.UUID("0199aaaa-0000-7000-8000-000000000003")


def test_agency_route_ignores_forged_tenant_id() -> None:
    resolved = resolve_route_tenant_id(
        principal_type=PrincipalType.AGENCY,
        membership_tenant_id=TENANT_A,
        claimed_tenant_id=TENANT_B,
        permissions=frozenset(),
    )
    assert resolved == TENANT_A


def test_missing_membership_tenant_fails_closed() -> None:
    with pytest.raises(DomainError) as exc:
        resolve_route_tenant_id(
            principal_type=PrincipalType.AGENCY,
            membership_tenant_id=None,
            claimed_tenant_id=TENANT_A,
            permissions=frozenset(),
        )
    assert exc.value.code == "tenant_route_denied"


def test_platform_route_requires_permission_and_explicit_id() -> None:
    with pytest.raises(DomainError) as exc:
        resolve_route_tenant_id(
            principal_type=PrincipalType.PLATFORM,
            membership_tenant_id=None,
            claimed_tenant_id=TENANT_A,
            permissions=frozenset(),
        )
    assert exc.value.code == "forbidden"
    resolved = resolve_route_tenant_id(
        principal_type=PrincipalType.PLATFORM,
        membership_tenant_id=None,
        claimed_tenant_id=TENANT_B,
        permissions=frozenset({"tenant.route"}),
    )
    assert resolved == TENANT_B


def test_suspended_tenant_is_not_routable() -> None:
    with pytest.raises(DomainError) as exc:
        assert_tenant_is_routable(TenantStatus.SUSPENDED)
    assert exc.value.code == "tenant_route_denied"
