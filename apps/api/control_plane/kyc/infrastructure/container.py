from __future__ import annotations

from control_plane.kyc.application.apply_webhook import ApplyKycWebhook
from control_plane.kyc.application.override_case import OverrideKycCase
from control_plane.kyc.application.request_payout import RequestPayout
from control_plane.kyc.application.start_session import StartKycSession
from control_plane.kyc.infrastructure.repositories import (
    DjangoKycCaseRepository,
    DjangoKycEventRepository,
    DjangoKycSettingsRepository,
)
from control_plane.tenancy.infrastructure.container import (
    change_agency_capabilities,
    tenant_repo,
)
from providers.kyc.hosted import HostedKycAdapter


def kyc_cases() -> DjangoKycCaseRepository:
    return DjangoKycCaseRepository()


def kyc_settings() -> DjangoKycSettingsRepository:
    return DjangoKycSettingsRepository()


def kyc_events() -> DjangoKycEventRepository:
    return DjangoKycEventRepository()


def kyc_provider() -> HostedKycAdapter:
    return HostedKycAdapter()


def start_kyc_session() -> StartKycSession:
    return StartKycSession(kyc_cases(), kyc_settings(), kyc_provider())


def apply_kyc_webhook() -> ApplyKycWebhook:
    return ApplyKycWebhook(kyc_cases(), kyc_events())


def override_kyc_case() -> OverrideKycCase:
    return OverrideKycCase(kyc_cases(), tenant_repo(), change_agency_capabilities())


def request_payout() -> RequestPayout:
    return RequestPayout(kyc_cases(), tenant_repo())
