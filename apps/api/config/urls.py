"""Root URLs. Public API is /api/v1/. Frozen Pipecat paths are /internal/telephony/v1/."""

from __future__ import annotations

from django.urls import include, path

from shared_kernel.http.health import liveness, readiness

urlpatterns = [
    path("health", liveness, name="health"),
    path("health/", liveness, name="health-slash"),
    path("ready", readiness, name="ready"),
    path("ready/", readiness, name="ready-slash"),
    path("api/v1/", include("config.api_urls")),
    path("webhooks/", include("control_plane.kyc.api.webhook_urls")),
    path("webhooks/", include("control_plane.billing.api.webhook_urls")),
    path(
        "internal/telephony/v1/",
        include("control_plane.telephony.api.internal_urls"),
    ),
    path(
        "internal/recordings/v1/",
        include("control_plane.recordings.api.internal_urls"),
    ),
]
