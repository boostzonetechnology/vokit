from __future__ import annotations

from datetime import UTC, datetime

import pytest

from control_plane.commission.domain.policies import hold_available_at
from control_plane.platform_settings.domain.policies import (
    assert_setting_key,
    coerce_value,
    public_value,
)
from shared_kernel.errors import DomainError


def test_hold_days_are_bounded_and_used() -> None:
    spec = assert_setting_key("payout.hold_days")
    assert coerce_value(spec, 21) == 21
    with pytest.raises(DomainError):
        coerce_value(spec, 400)
    earned = datetime(2026, 9, 1, tzinfo=UTC)
    assert hold_available_at(earned, 21) == datetime(2026, 9, 22, tzinfo=UTC)


def test_secret_settings_are_not_returned() -> None:
    spec = assert_setting_key("telephony.stt_api_key_ref")
    assert public_value(spec, "VOICE_STT_API_KEY") is None
