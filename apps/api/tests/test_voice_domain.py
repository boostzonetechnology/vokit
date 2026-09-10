from __future__ import annotations

from datetime import UTC, datetime

import pytest

from control_plane.telephony.domain.admission import decide_continue, normalize_did
from control_plane.telephony.domain.destinations import (
    AfterHoursAction,
    DestinationKind,
    after_hours_action,
    hunt_target,
    is_within_hours,
    parse_hours,
)
from shared_kernel.errors import DomainError


def test_normalize_did_accepts_digits_or_e164() -> None:
    assert normalize_did("14155550999") == "+14155550999"
    assert normalize_did("+1 (415) 555-0999") == "+14155550999"


def test_continue_stops_after_grace() -> None:
    decision = decide_continue(
        remaining_minutes=0,
        elapsed_seconds=31,
        overage_enabled=False,
        grace_seconds=30,
    )
    assert decision.continue_call is False
    assert decision.reason == "minutes_exhausted"


def test_continue_overage_keeps_call() -> None:
    decision = decide_continue(
        remaining_minutes=0,
        elapsed_seconds=120,
        overage_enabled=True,
        grace_seconds=0,
    )
    assert decision.continue_call is True
    assert decision.overage is True


def test_empty_hours_are_always_open() -> None:
    now = datetime(2026, 9, 10, 3, 0, tzinfo=UTC)
    assert is_within_hours(now, timezone_name="UTC", windows=()) is True


def test_hours_closed_maps_to_voicemail_or_reject() -> None:
    windows = parse_hours([{"weekday": 0, "start": "09:00", "end": "17:00"}])
    thursday = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    assert is_within_hours(thursday, timezone_name="UTC", windows=windows) is False
    assert after_hours_action(open_now=False, fallback_behavior="message") is (
        AfterHoursAction.VOICEMAIL
    )
    assert after_hours_action(open_now=False, fallback_behavior="hangup") is (
        AfterHoursAction.REJECT
    )


def test_queue_hunts_next_member() -> None:
    first = hunt_target(
        kind=DestinationKind.QUEUE,
        target="",
        members=(
            (DestinationKind.E164, "+15550001002"),
            (DestinationKind.SIP_CLIENT, "1002"),
        ),
        start_index=0,
    )
    assert first is not None
    assert first.to == "+15550001002"
    second = hunt_target(
        kind=DestinationKind.QUEUE,
        target="",
        members=(
            (DestinationKind.E164, "+15550001002"),
            (DestinationKind.SIP_CLIENT, "1002"),
        ),
        start_index=1,
    )
    assert second is not None
    assert second.to == "1002"
    assert hunt_target(
        kind=DestinationKind.QUEUE,
        target="",
        members=((DestinationKind.E164, "+15550001002"),),
        start_index=1,
    ) is None


def test_sip_client_rejects_non_numeric() -> None:
    with pytest.raises(DomainError):
        hunt_target(
            kind=DestinationKind.SIP_CLIENT,
            target="labphone",
            members=(),
        )
