from __future__ import annotations

from django.urls import path

from control_plane.reporting.api.views import (
    AgencyDashboardView,
    CustomerDashboardView,
    PlatformDashboardView,
)

urlpatterns = [
    path("platform/dashboard", PlatformDashboardView.as_view(), name="platform-dashboard"),
    path("agency/dashboard", AgencyDashboardView.as_view(), name="agency-dashboard"),
    path("customer/dashboard", CustomerDashboardView.as_view(), name="customer-dashboard"),
]
