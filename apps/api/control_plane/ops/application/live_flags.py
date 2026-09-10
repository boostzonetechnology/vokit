from __future__ import annotations

from control_plane.ops.domain.policies import feature_flag_disabled
from control_plane.platform_settings.infrastructure.container import platform_settings


def calling_is_live() -> bool:
    return platform_settings().live_flag("calling_live")


def billing_is_live() -> bool:
    return platform_settings().live_flag("billing_live")


def recordings_are_live() -> bool:
    return platform_settings().live_flag("recordings_live")


def assert_calling_live() -> None:
    if not calling_is_live():
        raise feature_flag_disabled("calling_live")


def assert_billing_live() -> None:
    if not billing_is_live():
        raise feature_flag_disabled("billing_live")


def assert_recordings_live() -> None:
    if not recordings_are_live():
        raise feature_flag_disabled("recordings_live")
