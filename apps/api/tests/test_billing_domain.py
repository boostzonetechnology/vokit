from __future__ import annotations

from datetime import UTC, datetime

import pytest

from control_plane.billing.domain.entitlements import assert_agent_cap, entitlements_tighter
from control_plane.billing.domain.lots import LotBalance, drain_lots, remaining_minutes
from control_plane.billing.domain.policies import (
    assert_invoice_total,
    assert_plan_version_mutable,
    line_is_commissionable,
)
from control_plane.billing.domain.proration import add_one_calendar_month, unused_credit_minor
from control_plane.billing.domain.types import LineKind, LotKind
from shared_kernel.errors import DomainError
from shared_kernel.money import Money


def test_drain_order_is_included_then_topup_then_overage() -> None:
    lots = (
        LotBalance("o1", LotKind.OVERAGE, 20),
        LotBalance("t1", LotKind.TOPUP, 10),
        LotBalance("i1", LotKind.INCLUDED, 5),
    )
    drains = drain_lots(lots, 12)
    assert [(item.lot_id, item.minutes) for item in drains] == [
        ("i1", 5),
        ("t1", 7),
    ]
    assert remaining_minutes(lots) == 35


def test_drain_rejects_when_lots_are_short() -> None:
    lots = (LotBalance("i1", LotKind.INCLUDED, 2),)
    with pytest.raises(DomainError) as exc:
        drain_lots(lots, 3)
    assert exc.value.code == "minutes_exhausted"


def test_invoice_total_is_sum_of_integer_lines() -> None:
    assert_invoice_total((Money(999), Money(1)), Money(1000))
    with pytest.raises(DomainError) as exc:
        assert_invoice_total((Money(50),), Money(40))
    assert exc.value.code == "invalid_invoice_total"


def test_used_plan_version_cannot_change() -> None:
    with pytest.raises(DomainError) as exc:
        assert_plan_version_mutable(used=True)
    assert exc.value.code == "plan_version_immutable"


def test_tax_is_not_commissionable_by_default() -> None:
    assert line_is_commissionable(LineKind.SUBSCRIPTION) is True
    assert line_is_commissionable(LineKind.TOPUP) is True
    assert line_is_commissionable(LineKind.TAX) is False
    assert line_is_commissionable(LineKind.PROMO) is False
    assert line_is_commissionable(LineKind.PASSTHROUGH) is False


def test_calendar_month_from_jan_31() -> None:
    start = datetime(2026, 1, 31, 12, 0, tzinfo=UTC)
    end = add_one_calendar_month(start)
    assert end.month == 2
    assert end.day == 28


def test_unused_credit_floors_and_is_zero_at_period_end() -> None:
    start = datetime(2026, 3, 1, 0, 0, tzinfo=UTC)
    mid = datetime(2026, 3, 16, 0, 0, tzinfo=UTC)
    end = add_one_calendar_month(start)
    credit = unused_credit_minor(price_minor=10000, period_start=start, now=mid)
    assert credit == (10000 * int((end - mid).total_seconds())) // int(
        (end - start).total_seconds()
    )
    assert unused_credit_minor(price_minor=10000, period_start=start, now=end) == 0


def test_agent_cap_unlimited_and_blocks_at_max() -> None:
    assert_agent_cap(max_agents=0, active_count=99)
    assert_agent_cap(max_agents=2, active_count=1)
    with pytest.raises(DomainError) as exc:
        assert_agent_cap(max_agents=1, active_count=1)
    assert exc.value.code == "plan_limit_agents"


def test_same_price_tighter_caps_count_as_downgrade() -> None:
    assert entitlements_tighter(
        new_max_agents=1,
        old_max_agents=0,
        new_max_phone_numbers=0,
        old_max_phone_numbers=0,
        new_max_concurrency=0,
        old_max_concurrency=0,
        new_recording_allowed=True,
        old_recording_allowed=True,
        new_integrations=(),
        old_integrations=(),
    )
    assert not entitlements_tighter(
        new_max_agents=0,
        old_max_agents=1,
        new_max_phone_numbers=0,
        old_max_phone_numbers=0,
        new_max_concurrency=0,
        old_max_concurrency=0,
        new_recording_allowed=True,
        old_recording_allowed=True,
        new_integrations=(),
        old_integrations=(),
    )
