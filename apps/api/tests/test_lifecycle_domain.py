from __future__ import annotations

import pytest

from control_plane.customers.domain.policies import BanKey, hash_ban_key
from control_plane.customers.domain.types import CustomerStatus, apply_customer_status_action
from control_plane.tenancy.domain.lifecycle import (
    AgencyCapabilities,
    AgencyStatus,
    apply_agency_status_action,
    assert_agency_may_create_customer,
    assert_agency_may_purchase_numbers,
)
from shared_kernel.errors import DomainError


def test_agency_status_transitions() -> None:
    assert apply_agency_status_action(AgencyStatus.INVITED, "activate") is AgencyStatus.ACTIVE
    assert apply_agency_status_action(AgencyStatus.ACTIVE, "suspend") is AgencyStatus.SUSPENDED
    assert apply_agency_status_action(AgencyStatus.SUSPENDED, "activate") is AgencyStatus.ACTIVE
    with pytest.raises(DomainError) as exc:
        apply_agency_status_action(AgencyStatus.CLOSED, "activate")
    assert exc.value.code == "agency_closed"


def test_default_capability_gates() -> None:
    from control_plane.tenancy.domain.lifecycle import (
        default_capabilities_for_status,
        merge_capability_gates,
    )

    current = AgencyCapabilities()
    restricted = merge_capability_gates(
        current, default_capabilities_for_status(AgencyStatus.RESTRICTED)
    )
    assert restricted.create_customers is False
    assert restricted.request_payouts is False
    assert restricted.create_agents is True
    review = merge_capability_gates(
        current, default_capabilities_for_status(AgencyStatus.UNDER_REVIEW)
    )
    assert review.request_payouts is False
    assert review.create_customers is True


def test_agency_create_customer_requires_active_for_agency_actor() -> None:
    caps = AgencyCapabilities()
    assert_agency_may_create_customer(AgencyStatus.ACTIVE, caps, privileged=False)
    with pytest.raises(DomainError):
        assert_agency_may_create_customer(
            AgencyStatus.RESTRICTED, caps, privileged=False
        )
    assert_agency_may_create_customer(AgencyStatus.RESTRICTED, caps, privileged=True)
    with pytest.raises(DomainError):
        assert_agency_may_create_customer(
            AgencyStatus.SUSPENDED, caps, privileged=True
        )


def test_agency_purchase_numbers_requires_capability() -> None:
    caps = AgencyCapabilities(purchase_numbers=False)
    with pytest.raises(DomainError) as exc:
        assert_agency_may_purchase_numbers(AgencyStatus.ACTIVE, caps, privileged=False)
    assert exc.value.code == "number_purchase_blocked"
    assert_agency_may_purchase_numbers(
        AgencyStatus.ACTIVE, AgencyCapabilities(), privileged=False
    )


def test_customer_status_agency_cannot_close() -> None:
    nxt = apply_customer_status_action(
        CustomerStatus.ACTIVE, "suspend", privileged=False
    )
    assert nxt is CustomerStatus.SUSPENDED
    with pytest.raises(DomainError) as exc:
        apply_customer_status_action(CustomerStatus.ACTIVE, "close", privileged=False)
    assert exc.value.code == "forbidden"


def test_ban_key_hash_is_stable() -> None:
    first = hash_ban_key(BanKey(kind="email", value="A@B.test"))
    second = hash_ban_key(BanKey(kind="email", value="a@b.test"))
    assert first == second
    assert len(first) == 64
