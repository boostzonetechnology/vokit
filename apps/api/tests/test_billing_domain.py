from __future__ import annotations

import pytest

from control_plane.billing.domain.lots import LotBalance, drain_lots, remaining_minutes
from control_plane.billing.domain.policies import (
    assert_invoice_total,
    assert_plan_version_mutable,
    line_is_commissionable,
)
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
