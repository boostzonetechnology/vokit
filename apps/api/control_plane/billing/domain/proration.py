from __future__ import annotations

import calendar
from datetime import datetime, timedelta


def add_one_calendar_month(value: datetime) -> datetime:
    month = value.month + 1
    year = value.year
    if month == 13:
        month = 1
        year += 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def period_end(period_start: datetime) -> datetime:
    return add_one_calendar_month(period_start)


def unused_credit_minor(
    *,
    price_minor: int,
    period_start: datetime,
    now: datetime,
) -> int:
    if price_minor < 1:
        return 0
    end = period_end(period_start)
    total = int((end - period_start).total_seconds())
    if total <= 0:
        return 0
    remaining = int((end - now).total_seconds())
    if remaining <= 0:
        return 0
    if remaining >= total:
        return price_minor
    return (price_minor * remaining) // total


def upgrade_due_at(now: datetime) -> datetime:
    return now + timedelta(days=1)
