from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from shared_kernel.errors import DomainError
from shared_kernel.time import utc_now

PERIODS = frozenset({"today", "7d", "30d", "mtd", "custom"})


@dataclass(frozen=True, slots=True)
class ReportWindow:
    period: str
    timezone: str
    start: datetime
    end: datetime


def parse_timezone(raw: str) -> ZoneInfo:
    name = (raw or "UTC").strip() or "UTC"
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise DomainError("validation_error", "timezone is invalid.") from exc


def parse_window(
    *,
    period: str,
    timezone: str,
    since: str = "",
    until: str = "",
    now: datetime | None = None,
) -> ReportWindow:
    name = (period or "30d").strip().lower()
    if name not in PERIODS:
        raise DomainError("validation_error", "period is invalid.")
    tz = parse_timezone(timezone)
    current = now or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=ZoneInfo("UTC"))
    local = current.astimezone(tz)
    end = local
    if name == "today":
        start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    elif name == "7d":
        start = local - timedelta(days=7)
    elif name == "30d":
        start = local - timedelta(days=30)
    elif name == "mtd":
        start = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        if not since or not until:
            raise DomainError("validation_error", "custom period requires since and until.")
        try:
            start = datetime.fromisoformat(since)
            end = datetime.fromisoformat(until)
        except ValueError as exc:
            raise DomainError("validation_error", "since/until is invalid.") from exc
        if start.tzinfo is None:
            start = start.replace(tzinfo=tz)
        if end.tzinfo is None:
            end = end.replace(tzinfo=tz)
        if end < start:
            raise DomainError("validation_error", "until must be after since.")
    return ReportWindow(period=name, timezone=str(tz), start=start, end=end)


def in_window(value: datetime | None, window: ReportWindow) -> bool:
    if value is None:
        return False
    stamp = value
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=ZoneInfo("UTC"))
    return window.start <= stamp <= window.end
