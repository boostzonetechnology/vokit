from __future__ import annotations

import pytest
from django.core.management import call_command

from control_plane.identity.demo import DEMO_AGENCY_EMAIL, DEMO_PLATFORM_EMAIL
from control_plane.identity.models import Membership, User


@pytest.mark.django_db
def test_seed_phase2_demo_creates_three_principals() -> None:
    call_command("seed_phase2_demo")
    assert User.objects.filter(email=DEMO_PLATFORM_EMAIL).exists()
    assert User.objects.filter(email=DEMO_AGENCY_EMAIL).exists()
    assert Membership.objects.filter(principal_type="platform").exists()
    assert Membership.objects.filter(principal_type="agency").exists()
    assert Membership.objects.filter(principal_type="customer").exists()


@pytest.mark.django_db
def test_bootstrap_platform_owner() -> None:
    call_command(
        "bootstrap_platform_owner",
        email="owner@vokit.test",
        password="Phase2-Owner!ok",
    )
    user = User.objects.get(email="owner@vokit.test")
    assert user.membership.role == "super_admin"
    assert user.membership.principal_type == "platform"
