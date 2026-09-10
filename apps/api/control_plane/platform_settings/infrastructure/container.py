from __future__ import annotations

from control_plane.platform_settings.application.service import PlatformSettingsControl
from control_plane.platform_settings.infrastructure.repositories import (
    DjangoAgencyFlagRepository,
    DjangoSettingRepository,
)


def platform_settings() -> PlatformSettingsControl:
    return PlatformSettingsControl(DjangoSettingRepository(), DjangoAgencyFlagRepository())
