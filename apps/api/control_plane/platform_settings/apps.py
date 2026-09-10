from __future__ import annotations

from django.apps import AppConfig


class PlatformSettingsConfig(AppConfig):
    name = "control_plane.platform_settings"
    label = "platform_settings"
    verbose_name = "Platform settings"
