from __future__ import annotations

from django.urls import path

from control_plane.platform_settings.api.views import (
    PlatformAgencyFlagView,
    PlatformSettingsView,
)

urlpatterns = [
    path("platform/settings", PlatformSettingsView.as_view(), name="platform-settings"),
    path(
        "platform/settings/flags",
        PlatformAgencyFlagView.as_view(),
        name="platform-settings-flags",
    ),
]
