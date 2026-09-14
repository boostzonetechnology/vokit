from __future__ import annotations

from django.urls import path

from control_plane.platform_settings.api.views import (
    AgencyTtsVoiceListView,
    CustomerTtsVoiceListView,
    PlatformAgencyFlagView,
    PlatformProviderModelsView,
    PlatformSettingsView,
    PlatformTtsVoiceListView,
)

urlpatterns = [
    path("platform/settings", PlatformSettingsView.as_view(), name="platform-settings"),
    path(
        "platform/settings/flags",
        PlatformAgencyFlagView.as_view(),
        name="platform-settings-flags",
    ),
    path("platform/tts/voices", PlatformTtsVoiceListView.as_view(), name="platform-tts-voices"),
    path("agency/tts/voices", AgencyTtsVoiceListView.as_view(), name="agency-tts-voices"),
    path("customer/tts/voices", CustomerTtsVoiceListView.as_view(), name="customer-tts-voices"),
    path(
        "platform/providers/<str:vendor>/models",
        PlatformProviderModelsView.as_view(),
        name="platform-provider-models",
    ),
]
