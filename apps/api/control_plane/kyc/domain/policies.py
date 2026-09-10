from __future__ import annotations

from control_plane.kyc.domain.types import KycStatus
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities, AgencyStatus
from shared_kernel.errors import DomainError


def map_provider_status(raw: str) -> KycStatus:
    from control_plane.kyc.domain.types import PROVIDER_STATUS_MAP

    key = (raw or "").strip().lower()
    status = PROVIDER_STATUS_MAP.get(key)
    if status is None:
        raise DomainError("kyc_status_unknown", "KYC status is unknown.", http_status=422)
    return status


def payout_unverified() -> DomainError:
    return DomainError(
        "payout_kyc_unverified",
        "Payout is not available.",
        http_status=409,
    )


def assert_payout_eligible(
    *,
    kyc_status: KycStatus | None,
    frozen: bool,
    agency_status: AgencyStatus,
    capabilities: AgencyCapabilities,
) -> None:
    if kyc_status is None or kyc_status is not KycStatus.VERIFIED:
        raise payout_unverified()
    if frozen:
        raise DomainError(
            "payout_kyc_frozen",
            "Payout is not available.",
            http_status=409,
        )
    if agency_status in {AgencyStatus.SUSPENDED, AgencyStatus.CLOSED}:
        raise DomainError(
            "payout_agency_blocked",
            "Payout is not available.",
            http_status=409,
        )
    if not capabilities.request_payouts:
        raise DomainError(
            "payout_agency_blocked",
            "Payout is not available.",
            http_status=409,
        )


def payout_block_reason(
    *,
    kyc_status: KycStatus | None,
    frozen: bool,
    agency_status: AgencyStatus,
    capabilities: AgencyCapabilities,
) -> str | None:
    try:
        assert_payout_eligible(
            kyc_status=kyc_status,
            frozen=frozen,
            agency_status=agency_status,
            capabilities=capabilities,
        )
    except DomainError as exc:
        return exc.code
    return None
