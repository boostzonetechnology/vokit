from __future__ import annotations

from django.urls import path

from control_plane.kyc.api.views import (
    AgencyKycSessionView,
    AgencyKycView,
    PlatformKycCaseCollectionView,
    PlatformKycOverrideView,
    PlatformKycSettingsView,
)

urlpatterns = [
    path("agency/kyc", AgencyKycView.as_view(), name="agency-kyc"),
    path(
        "agency/kyc/session",
        AgencyKycSessionView.as_view(),
        name="agency-kyc-session",
    ),
    path(
        "platform/kyc/cases",
        PlatformKycCaseCollectionView.as_view(),
        name="platform-kyc-cases",
    ),
    path(
        "platform/kyc/cases/<str:case_id>/override",
        PlatformKycOverrideView.as_view(),
        name="platform-kyc-override",
    ),
    path(
        "platform/kyc/settings",
        PlatformKycSettingsView.as_view(),
        name="platform-kyc-settings",
    ),
]
