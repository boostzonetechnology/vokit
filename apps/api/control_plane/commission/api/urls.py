from __future__ import annotations

from django.urls import path

from control_plane.commission.api.views import (
    AgencyPayoutCollectionView,
    AgencyPayoutMethodCollectionView,
    AgencyPayoutMethodDetailView,
    AgencyPayoutProofFileView,
    AgencyPayoutProofView,
    AgencyPayoutReceiptView,
    AgencyWalletView,
    PlatformPayoutActionView,
    PlatformPayoutCollectionView,
    PlatformPayoutDetailView,
    PlatformPayoutMarkPaidView,
    PlatformPayoutProofFileView,
    PlatformPayoutProofView,
    PlatformReverseCommissionView,
    PlatformWalletAdjustView,
    PlatformWalletFreezeView,
    PlatformWalletView,
)

urlpatterns = [
    path("agency/wallet", AgencyWalletView.as_view(), name="agency-wallet"),
    path("agency/payouts", AgencyPayoutCollectionView.as_view(), name="agency-payouts"),
    path(
        "agency/payout-methods",
        AgencyPayoutMethodCollectionView.as_view(),
        name="agency-payout-methods",
    ),
    path(
        "agency/payout-methods/<str:method_id>",
        AgencyPayoutMethodDetailView.as_view(),
        name="agency-payout-method-detail",
    ),
    path(
        "agency/payouts/<str:payout_id>/receipt",
        AgencyPayoutReceiptView.as_view(),
        name="agency-payout-receipt",
    ),
    path(
        "agency/payouts/<str:payout_id>/proof",
        AgencyPayoutProofView.as_view(),
        name="agency-payout-proof",
    ),
    path(
        "agency/payouts/<str:payout_id>/proof/file",
        AgencyPayoutProofFileView.as_view(),
        name="agency-payout-proof-file",
    ),
    path(
        "platform/agencies/<str:agency_id>/wallet",
        PlatformWalletView.as_view(),
        name="platform-agency-wallet",
    ),
    path(
        "platform/agencies/<str:agency_id>/wallet/adjust",
        PlatformWalletAdjustView.as_view(),
        name="platform-wallet-adjust",
    ),
    path(
        "platform/agencies/<str:agency_id>/wallet/freeze",
        PlatformWalletFreezeView.as_view(),
        name="platform-wallet-freeze",
    ),
    path("platform/payouts", PlatformPayoutCollectionView.as_view(), name="platform-payouts"),
    path(
        "platform/payouts/<str:payout_id>",
        PlatformPayoutDetailView.as_view(),
        name="platform-payout-detail",
    ),
    path(
        "platform/payouts/<str:payout_id>/action",
        PlatformPayoutActionView.as_view(),
        name="platform-payout-action",
    ),
    path(
        "platform/payouts/<str:payout_id>/proof",
        PlatformPayoutProofView.as_view(),
        name="platform-payout-proof",
    ),
    path(
        "platform/payouts/<str:payout_id>/proof/file",
        PlatformPayoutProofFileView.as_view(),
        name="platform-payout-proof-file",
    ),
    path(
        "platform/payouts/<str:payout_id>/mark-paid",
        PlatformPayoutMarkPaidView.as_view(),
        name="platform-payout-mark-paid",
    ),
    path(
        "platform/commissions/reverse",
        PlatformReverseCommissionView.as_view(),
        name="platform-commission-reverse",
    ),
]
