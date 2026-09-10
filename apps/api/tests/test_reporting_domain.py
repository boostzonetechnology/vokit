from __future__ import annotations

from datetime import UTC, datetime

import pytest

from control_plane.reporting.domain.periods import in_window, parse_window
from shared_kernel.errors import DomainError


def test_standard_periods_use_explicit_timezone() -> None:
    now = datetime(2026, 9, 10, 15, 0, tzinfo=UTC)
    today = parse_window(period="today", timezone="UTC", now=now)
    assert today.start.day == 10
    week = parse_window(period="7d", timezone="UTC", now=now)
    assert (now - week.start).days == 7
    mtd = parse_window(period="mtd", timezone="UTC", now=now)
    assert mtd.start.day == 1
    custom = parse_window(
        period="custom",
        timezone="UTC",
        since="2026-09-01T00:00:00+00:00",
        until="2026-09-10T00:00:00+00:00",
        now=now,
    )
    assert in_window(datetime(2026, 9, 5, tzinfo=UTC), custom) is True
    assert in_window(datetime(2026, 8, 1, tzinfo=UTC), custom) is False


def test_invalid_period_and_range_fail_closed() -> None:
    with pytest.raises(DomainError):
        parse_window(period="year", timezone="UTC")
    with pytest.raises(DomainError):
        parse_window(period="custom", timezone="UTC", since="", until="")
    with pytest.raises(DomainError):
        parse_window(period="today", timezone="Not/AZone")
