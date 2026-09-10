from __future__ import annotations

import pytest

from shared_kernel.errors import DomainError
from shared_kernel.money import Money, money_from_major_decimal_string


def test_rejects_float_minor_units() -> None:
    with pytest.raises(DomainError) as exc:
        Money(10.0)  # type: ignore[arg-type]
    assert exc.value.code == "invalid_money"


def test_rejects_non_usd() -> None:
    with pytest.raises(DomainError) as exc:
        Money(100, "EUR")
    assert exc.value.code == "unsupported_currency"


def test_add_and_subtract() -> None:
    assert (Money(199) + Money(1)).minor_units == 200
    assert (Money(199) - Money(99)).minor_units == 100


def test_parse_decimal_without_float() -> None:
    assert money_from_major_decimal_string("10.50").minor_units == 1050
    assert money_from_major_decimal_string("-2").minor_units == -200
    assert money_from_major_decimal_string("0.05").minor_units == 5


def test_parse_rejects_three_places() -> None:
    with pytest.raises(DomainError):
        money_from_major_decimal_string("1.999")
