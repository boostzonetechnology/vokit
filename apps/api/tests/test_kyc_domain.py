from __future__ import annotations

import pytest

from control_plane.kyc.domain.policies import assert_payout_eligible, map_provider_status
from control_plane.kyc.domain.types import KycStatus
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities, AgencyStatus
from shared_kernel.errors import DomainError


def test_unknown_provider_status_fails_closed() -> None:
    with pytest.raises(DomainError) as exc:
        map_provider_status("approved_please")
    assert exc.value.code == "kyc_status_unknown"


def test_payout_requires_verified_and_unfrozen() -> None:
    caps = AgencyCapabilities()
    assert_payout_eligible(
        kyc_status=KycStatus.VERIFIED,
        frozen=False,
        agency_status=AgencyStatus.ACTIVE,
        capabilities=caps,
    )
    with pytest.raises(DomainError) as exc:
        assert_payout_eligible(
            kyc_status=None,
            frozen=False,
            agency_status=AgencyStatus.ACTIVE,
            capabilities=caps,
        )
    assert exc.value.code == "payout_kyc_unverified"
    with pytest.raises(DomainError) as exc:
        assert_payout_eligible(
            kyc_status=KycStatus.VERIFIED,
            frozen=True,
            agency_status=AgencyStatus.ACTIVE,
            capabilities=caps,
        )
    assert exc.value.code == "payout_kyc_frozen"
