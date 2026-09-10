from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from control_plane.telephony.domain.admission import normalize_did
from shared_kernel.errors import DomainError


class DestinationKind(StrEnum):
    E164 = "e164"
    DEPARTMENT = "department"
    QUEUE = "queue"
    SIP_CLIENT = "sip_client"


class DestinationStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class AfterHoursAction(StrEnum):
    OPEN = "open"
    VOICEMAIL = "voicemail"
    TRANSFER = "transfer"
    REJECT = "outside_hours"


@dataclass(frozen=True, slots=True)
class HoursWindow:
    weekday: int
    start: str
    end: str


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    kind: DestinationKind
    to: str
    label: str
    destination_id: str
    member_index: int = 0


def assert_destination_kind(raw: str) -> DestinationKind:
    try:
        return DestinationKind((raw or "").strip().lower())
    except ValueError as exc:
        raise DomainError("validation_error", "destination kind is invalid.") from exc


def assert_sip_extension(raw: str) -> str:
    compact = "".join(ch for ch in (raw or "").strip() if ch.isdigit())
    if len(compact) < 2 or len(compact) > 16:
        raise DomainError("validation_error", "SIP client target must be a numeric extension.")
    return compact


def edge_target(kind: DestinationKind, target: str) -> str:
    if kind is DestinationKind.SIP_CLIENT:
        return assert_sip_extension(target)
    if kind in {DestinationKind.E164, DestinationKind.DEPARTMENT}:
        return normalize_did(target)
    raise DomainError("validation_error", "queue destinations resolve through members.")


def parse_hours(raw: object) -> tuple[HoursWindow, ...]:
    if raw in (None, "", []):
        return ()
    if type(raw) is not list:
        raise DomainError("validation_error", "business_hours must be a list.")
    windows: list[HoursWindow] = []
    for item in raw:
        if type(item) is not dict:
            raise DomainError("validation_error", "business_hours entries must be objects.")
        weekday = item.get("weekday")
        if type(weekday) is not int or weekday < 0 or weekday > 6:
            raise DomainError("validation_error", "weekday must be an integer 0-6.")
        start = str(item.get("start") or "").strip()
        end = str(item.get("end") or "").strip()
        _parse_hhmm(start)
        _parse_hhmm(end)
        windows.append(HoursWindow(weekday=weekday, start=start, end=end))
    return tuple(windows)


def is_within_hours(
    now: datetime, *, timezone_name: str, windows: tuple[HoursWindow, ...]
) -> bool:
    if not windows:
        return True
    try:
        zone = ZoneInfo((timezone_name or "UTC").strip() or "UTC")
    except ZoneInfoNotFoundError as exc:
        raise DomainError("validation_error", "timezone is invalid.") from exc
    local = now.astimezone(zone) if now.tzinfo else now.replace(tzinfo=zone)
    weekday = local.weekday()
    current = local.strftime("%H:%M")
    for window in windows:
        if window.weekday != weekday:
            continue
        if window.start <= current < window.end:
            return True
    return False


def after_hours_action(*, open_now: bool, fallback_behavior: str) -> AfterHoursAction:
    if open_now:
        return AfterHoursAction.OPEN
    fallback = (fallback_behavior or "").strip().lower()
    if fallback == "message":
        return AfterHoursAction.VOICEMAIL
    if fallback == "transfer":
        return AfterHoursAction.TRANSFER
    return AfterHoursAction.REJECT


def hunt_target(
    *,
    kind: DestinationKind,
    target: str,
    members: tuple[tuple[DestinationKind, str], ...],
    start_index: int = 0,
) -> ResolvedTarget | None:
    if kind is DestinationKind.QUEUE:
        if start_index < 0:
            start_index = 0
        for index, (member_kind, member_target) in enumerate(members):
            if index < start_index:
                continue
            if member_kind is DestinationKind.QUEUE:
                continue
            return ResolvedTarget(
                kind=member_kind,
                to=edge_target(member_kind, member_target),
                label=member_target,
                destination_id="",
                member_index=index,
            )
        return None
    return ResolvedTarget(
        kind=kind,
        to=edge_target(kind, target),
        label=target,
        destination_id="",
        member_index=0,
    )


def _parse_hhmm(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise DomainError("validation_error", "hours must use HH:MM.")
    hour = int(parts[0])
    minute = int(parts[1])
    if hour > 23 or minute > 59:
        raise DomainError("validation_error", "hours must use HH:MM.")
    return hour, minute
