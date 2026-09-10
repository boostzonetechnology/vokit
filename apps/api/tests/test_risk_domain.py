from __future__ import annotations

import pytest

from control_plane.risk.domain.policies import (
    CardMaskAssessment,
    assert_agency_cannot_override,
    assert_card_mask,
    assert_commercially_open,
    assert_no_sensitive_card_payload,
)
from control_plane.risk.domain.types import RiskStatus
from shared_kernel.errors import DomainError


def test_card_mask_accepts_last_four_only() -> None:
    assert_card_mask(
        CardMaskAssessment(
            last4="4242",
            visible_digit_count=4,
            cvv_visible=False,
            full_pan_present=False,
        )
    )


def test_over_exposed_card_image_is_rejected() -> None:
    with pytest.raises(DomainError) as exc:
        assert_card_mask(
            CardMaskAssessment(
                last4="4242",
                visible_digit_count=16,
                cvv_visible=False,
                full_pan_present=False,
            )
        )
    assert exc.value.code == "card_image_unmasked"
    assert exc.value.http_status == 422
    assert "last four digits" in exc.value.message


def test_cvv_or_full_pan_is_rejected() -> None:
    with pytest.raises(DomainError) as exc:
        assert_card_mask(
            CardMaskAssessment(
                last4="4242",
                visible_digit_count=4,
                cvv_visible=True,
                full_pan_present=False,
            )
        )
    assert exc.value.code == "card_image_unmasked"


def test_sensitive_card_keys_are_rejected() -> None:
    with pytest.raises(DomainError) as exc:
        assert_no_sensitive_card_payload({"card_last4": "4242", "cvv": "123"})
    assert exc.value.code == "prohibited_card_data"


def test_frozen_and_banned_block_commercial_activity() -> None:
    with pytest.raises(DomainError) as exc:
        assert_commercially_open(RiskStatus.CHARGEBACK_FROZEN)
    assert exc.value.code == "customer_risk_blocked"
    with pytest.raises(DomainError):
        assert_commercially_open(RiskStatus.VERIFIED, permanently_banned=True)
    assert_commercially_open(RiskStatus.NORMAL)
    assert_commercially_open(RiskStatus.VERIFIED)


def test_agency_cannot_override_risk() -> None:
    with pytest.raises(DomainError) as exc:
        assert_agency_cannot_override()
    assert exc.value.code == "forbidden"
    assert exc.value.http_status == 403
