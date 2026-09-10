from __future__ import annotations

from django.urls import path

from control_plane.telephony.api.views import (
    AgencyCallCollectionView,
    AgencyNumberAssignView,
    AgencyNumberCollectionView,
    AgencyNumberReleaseView,
    AgencyNumberReserveView,
    AgencyNumberSearchView,
    AgencyOutboundCallView,
    AgencyTransferCollectionView,
    AgencyTransferDisableView,
    CustomerCallCollectionView,
    PlatformCallCollectionView,
    PlatformNumberCollectionView,
    PlatformNumberReconcileView,
    PlatformNumberReleaseView,
    PlatformTransferCollectionView,
    PlatformTransferDisableView,
)

urlpatterns = [
    path("platform/calls", PlatformCallCollectionView.as_view(), name="platform-calls"),
    path(
        "platform/transfers",
        PlatformTransferCollectionView.as_view(),
        name="platform-transfers",
    ),
    path(
        "platform/transfers/<str:destination_id>/disable",
        PlatformTransferDisableView.as_view(),
        name="platform-transfer-disable",
    ),
    path(
        "platform/phone-numbers",
        PlatformNumberCollectionView.as_view(),
        name="platform-phone-numbers",
    ),
    path(
        "platform/phone-numbers/reconcile",
        PlatformNumberReconcileView.as_view(),
        name="platform-phone-numbers-reconcile",
    ),
    path(
        "platform/phone-numbers/<str:number_id>/release",
        PlatformNumberReleaseView.as_view(),
        name="platform-phone-number-release",
    ),
    path(
        "agency/phone-numbers",
        AgencyNumberCollectionView.as_view(),
        name="agency-phone-numbers",
    ),
    path(
        "agency/phone-numbers/search",
        AgencyNumberSearchView.as_view(),
        name="agency-phone-numbers-search",
    ),
    path(
        "agency/phone-numbers/reservations",
        AgencyNumberReserveView.as_view(),
        name="agency-phone-number-reservations",
    ),
    path(
        "agency/phone-numbers/assignments",
        AgencyNumberAssignView.as_view(),
        name="agency-phone-number-assignments",
    ),
    path(
        "agency/phone-numbers/<str:number_id>/release",
        AgencyNumberReleaseView.as_view(),
        name="agency-phone-number-release",
    ),
    path("agency/transfers", AgencyTransferCollectionView.as_view(), name="agency-transfers"),
    path(
        "agency/transfers/<str:destination_id>/disable",
        AgencyTransferDisableView.as_view(),
        name="agency-transfer-disable",
    ),
    path("agency/calls", AgencyCallCollectionView.as_view(), name="agency-calls"),
    path(
        "agency/calls/outbound",
        AgencyOutboundCallView.as_view(),
        name="agency-calls-outbound",
    ),
    path("customer/calls", CustomerCallCollectionView.as_view(), name="customer-calls"),
]
