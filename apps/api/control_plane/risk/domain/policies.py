from __future__ import annotations

from dataclasses import dataclass

from control_plane.risk.domain.types import COMMERCIALLY_BLOCKED, RiskStatus
from shared_kernel.errors import DomainError


@dataclass(frozen=True, slots=True)
class CardMaskAssessment:
    last4: str
    visible_digit_count: int
    cvv_visible: bool
    full_pan_present: bool


def assert_card_mask(assessment: CardMaskAssessment) -> None:
    last4 = (assessment.last4 or "").strip()
    if len(last4) != 4 or not last4.isdigit():
        raise DomainError("validation_error", "Card last four digits are required.")
    if type(assessment.visible_digit_count) is not int:
        raise DomainError("validation_error", "visible_digit_count must be an integer.")
    exposed = (
        assessment.full_pan_present
        or assessment.cvv_visible
        or assessment.visible_digit_count > 4
    )
    if exposed:
        raise DomainError(
            "card_image_unmasked",
            "Your card image cannot be accepted because sensitive card-number "
            "information is visible. Please hide all card-number digits except "
            "the last four digits and upload the image again.",
            http_status=422,
        )


def assert_commercially_open(
    status: RiskStatus | None, *, permanently_banned: bool = False
) -> None:
    if permanently_banned:
        raise DomainError(
            "customer_risk_blocked",
            "Customer commercial activity is not available.",
            http_status=409,
        )
    if status is None or status is RiskStatus.NORMAL or status is RiskStatus.VERIFIED:
        return
    if status in COMMERCIALLY_BLOCKED:
        raise DomainError(
            "customer_risk_blocked",
            "Customer commercial activity is not available.",
            http_status=409,
        )


def assert_agency_cannot_override() -> None:
    raise DomainError("forbidden", "Not permitted.", http_status=403)


def assert_no_sensitive_card_payload(data: dict) -> None:
    keys = {str(key).strip().lower() for key in data}
    forbidden = {"pan", "primary_account", "cvv", "cvc", "pin", "track", "card_number"}
    if keys & forbidden:
        raise DomainError(
            "prohibited_card_data",
            "Full card numbers and security codes must not be submitted.",
            http_status=422,
        )
