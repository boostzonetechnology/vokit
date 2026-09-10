from __future__ import annotations

from control_plane.billing.infrastructure.container import invoice_index, tenant_billing
from control_plane.commission.application.accrue import AccrueCommission
from control_plane.commission.application.adjust import AdjustWallet
from control_plane.commission.application.freeze import FreezeWallet
from control_plane.commission.application.payout import (
    DecidePayout,
    RequestAgencyPayout,
    UploadPayoutProof,
)
from control_plane.commission.application.reconcile import ReconcileFinance
from control_plane.commission.application.release_holds import ReleaseHolds
from control_plane.commission.application.reverse import ReverseCommission
from control_plane.commission.infrastructure.repositories import (
    DjangoCommissionIdempotencyRepository,
    DjangoLedgerRepository,
    DjangoPayoutProofRepository,
    DjangoPayoutRepository,
)
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.kyc.infrastructure.container import kyc_cases
from control_plane.tenancy.infrastructure.container import tenant_repo


def ledger() -> DjangoLedgerRepository:
    return DjangoLedgerRepository()


def payouts() -> DjangoPayoutRepository:
    return DjangoPayoutRepository()


def proofs() -> DjangoPayoutProofRepository:
    return DjangoPayoutProofRepository()


def keys() -> DjangoCommissionIdempotencyRepository:
    return DjangoCommissionIdempotencyRepository()


def accrue_commission() -> AccrueCommission:
    from control_plane.platform_settings.infrastructure.container import (
        platform_settings,
    )

    return AccrueCommission(ledger(), tenant_repo(), hold_days=platform_settings().hold_days())


def reverse_commission() -> ReverseCommission:
    return ReverseCommission(ledger(), SystemClock())


def release_holds() -> ReleaseHolds:
    return ReleaseHolds(ledger(), tenant_repo(), SystemClock())


def adjust_wallet() -> AdjustWallet:
    return AdjustWallet(ledger(), SystemClock())


def freeze_wallet() -> FreezeWallet:
    return FreezeWallet(ledger(), SystemClock())


def request_payout() -> RequestAgencyPayout:
    return RequestAgencyPayout(
        ledger(),
        payouts(),
        keys(),
        kyc_cases(),
        tenant_repo(),
        SystemClock(),
    )


def decide_payout() -> DecidePayout:
    return DecidePayout(ledger(), payouts(), proofs(), SystemClock())


def upload_proof() -> UploadPayoutProof:
    return UploadPayoutProof(payouts(), proofs())


def reconcile_finance() -> ReconcileFinance:
    return ReconcileFinance(
        invoice_index(),
        ledger(),
        payouts(),
        tenant_billing(),
        accrue_commission(),
    )
