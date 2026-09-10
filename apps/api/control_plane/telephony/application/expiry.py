from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from control_plane.telephony.application.ports import (
    PhoneNumberRecord,
    PhoneNumberRepository,
    ReservationRepository,
)
from control_plane.telephony.domain.policies import reservation_is_active
from control_plane.telephony.domain.types import NumberStatus, ReservationStatus


def expire_number_if_stale(
    numbers: PhoneNumberRepository,
    reservations: ReservationRepository,
    record: PhoneNumberRecord,
    now: datetime,
) -> PhoneNumberRecord:
    if record.status is not NumberStatus.RESERVED:
        return record
    reservation = None
    if record.reservation_id is not None:
        reservation = reservations.get(record.reservation_id)
    if reservation is not None and reservation_is_active(
        status=reservation.status, expires_at=reservation.expires_at, now=now
    ):
        return record
    if reservation is not None and reservation.status is ReservationStatus.ACTIVE:
        reservations.save(replace(reservation, status=ReservationStatus.EXPIRED))
    return numbers.save(
        replace(
            record,
            status=NumberStatus.AVAILABLE,
            reservation_id=None,
            reserved_until=None,
            updated_at=now,
        )
    )


def expire_stale_reservations(
    numbers: PhoneNumberRepository,
    reservations: ReservationRepository,
    now: datetime,
) -> int:
    expired = 0
    for reservation in reservations.list_expired(now):
        number = numbers.get(reservation.number_id)
        if number is None:
            reservations.save(replace(reservation, status=ReservationStatus.EXPIRED))
            expired += 1
            continue
        updated = expire_number_if_stale(numbers, reservations, number, now)
        if updated.status is NumberStatus.AVAILABLE:
            expired += 1
    return expired
