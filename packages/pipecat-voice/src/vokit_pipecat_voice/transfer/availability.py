"""Transfer availability checks (mirrors Django transfer_numbers.services.availability)."""
from __future__ import annotations

import logging
from datetime import datetime, time, timezone as dt_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

VALID_WEEKDAYS = frozenset(range(7))


def _resolve_tz(tz_name: str):
    name = (tz_name or "UTC").strip() or "UTC"
    if name.upper() == "UTC":
        return dt_timezone.utc
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        logger.warning(
            "transfer availability: timezone %r unavailable (install tzdata package)",
            name,
        )
        return None


def _parse_time(value: str) -> time | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        hour, minute = raw.split(":", 1)
        return time(int(hour), int(minute))
    except (TypeError, ValueError):
        return None


def is_available_from_spec(spec: dict, *, now: datetime | None = None) -> bool:
    """Check bootstrap transfer.availability against current time."""
    if not spec:
        return False
    days_raw = spec.get("days") or spec.get("availability_days") or []
    try:
        days = {int(d) for d in days_raw if int(d) in VALID_WEEKDAYS}
    except (TypeError, ValueError):
        days = set()
    if not days:
        return False
    start = _parse_time(str(spec.get("start") or spec.get("availability_start") or ""))
    end = _parse_time(str(spec.get("end") or spec.get("availability_end") or ""))
    if start is None or end is None or start == end:
        return False
    tz_name = (spec.get("timezone") or "UTC").strip() or "UTC"
    tz = _resolve_tz(tz_name)
    if tz is None:
        return False
    moment = now or datetime.now(tz=dt_timezone.utc)
    local = moment.astimezone(tz)
    if local.weekday() not in days:
        return False
    current = local.time()
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end
