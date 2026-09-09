"""Transfer availability helper (mirrors Django)."""
from __future__ import annotations

from datetime import datetime, timezone

from vokit_pipecat_voice.transfer.availability import is_available_from_spec


def test_available_on_matching_day_and_hour():
    spec = {
        "days": [0],
        "start": "20:00",
        "end": "22:00",
        "timezone": "UTC",
    }
    monday_ok = datetime(2026, 8, 17, 21, 0, tzinfo=timezone.utc)
    tuesday_no = datetime(2026, 8, 18, 21, 0, tzinfo=timezone.utc)
    assert is_available_from_spec(spec, now=monday_ok) is True
    assert is_available_from_spec(spec, now=tuesday_no) is False


def test_empty_spec_not_available():
    assert is_available_from_spec({}) is False
    assert is_available_from_spec({"days": [], "start": "09:00", "end": "17:00"}) is False


def test_asia_karachi_window():
    spec = {
        "days": [0, 1, 2, 3, 4],
        "start": "21:00",
        "end": "23:47",
        "timezone": "Asia/Karachi",
    }
    in_window = datetime(2026, 8, 19, 17, 10, tzinfo=timezone.utc)  # 22:10 PKT Wed
    out_window = datetime(2026, 8, 19, 14, 0, tzinfo=timezone.utc)  # 19:00 PKT
    assert is_available_from_spec(spec, now=in_window) is True
    assert is_available_from_spec(spec, now=out_window) is False
