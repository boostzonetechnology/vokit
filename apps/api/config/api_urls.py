"""Versioned public API. Tenant routing is server-side only."""

from __future__ import annotations

from django.urls import include, path

from shared_kernel.http.health import liveness

urlpatterns = [
    path("health", liveness, name="api-v1-health"),
    path("health/", liveness, name="api-v1-health-slash"),
    path("", include("control_plane.identity.api.urls")),
    path("", include("control_plane.tenancy.api.urls")),
    path("", include("control_plane.customers.api.urls")),
    path("", include("control_plane.kyc.api.urls")),
    path("", include("control_plane.billing.api.urls")),
    path("", include("control_plane.commission.api.urls")),
    path("", include("control_plane.risk.api.urls")),
    path("", include("control_plane.agents.api.urls")),
    path("", include("control_plane.telephony.api.urls")),
    path("", include("control_plane.recordings.api.urls")),
    path("", include("control_plane.integrations.api.urls")),
    path("", include("control_plane.audit.api.urls")),
    path("", include("control_plane.notifications.api.urls")),
    path("", include("control_plane.platform_settings.api.urls")),
    path("", include("control_plane.reporting.api.urls")),
]
