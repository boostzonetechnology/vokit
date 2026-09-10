from __future__ import annotations

from datetime import datetime, timedelta

from control_plane.telephony.domain.types import (
    RESERVATION_SECONDS,
    NumberStatus,
    ReservationStatus,
)
from shared_kernel.errors import DomainError
from shared_kernel.phone import normalize_e164


def number_e164(raw: str) -> str:
    return normalize_e164(raw)


def reservation_deadline(now: datetime, *, seconds: int = RESERVATION_SECONDS) -> datetime:
    if type(seconds) is not int or seconds <= 0:
        raise DomainError("validation_error", "Reservation window is invalid.")
    return now + timedelta(seconds=seconds)


def reservation_is_active(
    *,
    status: ReservationStatus,
    expires_at: datetime,
    now: datetime,
) -> bool:
    return status is ReservationStatus.ACTIVE and expires_at > now


def assert_available_for_reserve(*, status: NumberStatus) -> None:
    if status is NumberStatus.AVAILABLE:
        return
    if status is NumberStatus.RESERVED:
        raise number_reserved()
    if status is NumberStatus.ASSIGNED:
        raise DomainError(
            "number_assigned",
            "Number is already assigned.",
            http_status=409,
        )
    raise DomainError(
        "number_unavailable",
        "Number is not available.",
        http_status=409,
        details={"status": status.value},
    )


def assert_one_routing_target(*, assigned_agent_id) -> None:
    if assigned_agent_id is not None:
        raise DomainError(
            "number_assigned",
            "A number can have only one active routing target.",
            http_status=409,
        )


def assert_release_confirmed(confirm: bool) -> None:
    if confirm is not True:
        raise DomainError(
            "release_confirmation_required",
            "Release requires explicit confirmation.",
            http_status=422,
        )


def assert_assign_confirmed(confirm: bool) -> None:
    if confirm is not True:
        raise DomainError(
            "assign_confirmation_required",
            "Assignment requires explicit confirmation.",
            http_status=422,
        )


def number_reserved() -> DomainError:
    return DomainError(
        "number_reserved",
        "Number is reserved by another agency.",
        http_status=409,
    )


def number_not_found() -> DomainError:
    return DomainError("not_found", "Resource not found.", http_status=404)


def parse_capabilities(raw: object) -> tuple[str, ...]:
    if raw is None or raw == "":
        return ("voice",)
    if isinstance(raw, str):
        items = [part.strip().lower() for part in raw.split(",") if part.strip()]
    elif isinstance(raw, (list, tuple)):
        items = [str(part).strip().lower() for part in raw if str(part).strip()]
    else:
        raise DomainError("validation_error", "capabilities is invalid.")
    allowed = {"voice", "sms", "mms"}
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in allowed:
            raise DomainError("validation_error", f"Capability '{item}' is not supported.")
        if item not in seen:
            seen.add(item)
            cleaned.append(item)
    return tuple(cleaned or ["voice"])
