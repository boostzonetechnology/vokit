from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from control_plane.telephony.domain.policies import (
    assert_available_for_reserve,
    assert_one_routing_target,
    assert_release_confirmed,
    number_e164,
    reservation_deadline,
    reservation_is_active,
)
from control_plane.telephony.domain.types import (
    RESERVATION_SECONDS,
    NumberStatus,
    ReservationStatus,
)
from shared_kernel.errors import DomainError
from shared_kernel.time import utc_now


def test_reservation_window_is_ten_minutes() -> None:
    now = utc_now()
    deadline = reservation_deadline(now)
    assert deadline - now == timedelta(seconds=RESERVATION_SECONDS)
    assert RESERVATION_SECONDS == 600


def test_active_reservation_blocks_until_expiry() -> None:
    now = datetime(2026, 9, 10, 12, 0, tzinfo=now_tz())
    expires = now + timedelta(minutes=10)
    assert reservation_is_active(
        status=ReservationStatus.ACTIVE, expires_at=expires, now=now
    )
    assert not reservation_is_active(
        status=ReservationStatus.ACTIVE,
        expires_at=expires,
        now=now + timedelta(minutes=10, seconds=1),
    )


def now_tz():
    return utc_now().tzinfo


def test_reserved_number_cannot_be_taken() -> None:
    with pytest.raises(DomainError) as exc:
        assert_available_for_reserve(status=NumberStatus.RESERVED)
    assert exc.value.code == "number_reserved"


def test_one_active_routing_target() -> None:
    with pytest.raises(DomainError) as exc:
        assert_one_routing_target(assigned_agent_id="already-set")
    assert exc.value.code == "number_assigned"


def test_release_requires_confirmation() -> None:
    with pytest.raises(DomainError) as exc:
        assert_release_confirmed(False)
    assert exc.value.code == "release_confirmation_required"


def test_inventory_stores_e164() -> None:
    assert number_e164("+1 (415) 555-0100") == "+14155550100"
