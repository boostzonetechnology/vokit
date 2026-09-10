"""Integer minor units. USD only in V1 (Q-005, NFR-011). Never float."""

from __future__ import annotations

from dataclasses import dataclass

from shared_kernel.errors import DomainError

V1_CURRENCY = "USD"


@dataclass(frozen=True, slots=True)
class Money:
    minor_units: int
    currency: str = V1_CURRENCY

    def __post_init__(self) -> None:
        if type(self.minor_units) is not int:
            raise DomainError("invalid_money", "Monetary amounts must be integer minor units.")
        if self.currency != V1_CURRENCY:
            raise DomainError("unsupported_currency", "V1 supports USD only.")

    def __add__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.minor_units + other.minor_units, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.minor_units - other.minor_units, self.currency)

    def _same_currency(self, other: Money) -> None:
        if not isinstance(other, Money) or other.currency != self.currency:
            raise DomainError(
                "currency_mismatch",
                "Cannot combine amounts in different currencies.",
            )


def money_from_major_decimal_string(amount: str, currency: str = V1_CURRENCY) -> Money:
    """Parse a display decimal like '10.00' without binary float."""
    text = amount.strip()
    if not text:
        raise DomainError("invalid_money", "Amount must be a decimal with at most two places.")
    sign = 1
    if text[0] == "-":
        sign = -1
        text = text[1:]
    if not text:
        raise DomainError("invalid_money", "Amount must be a decimal with at most two places.")
    if "." in text:
        whole, frac = text.split(".", 1)
        if not whole:
            whole = "0"
        if not whole.isdigit() or not frac.isdigit() or len(frac) > 2:
            raise DomainError("invalid_money", "Amount must be a decimal with at most two places.")
        frac = frac.ljust(2, "0")
        minor = int(whole) * 100 + int(frac)
    else:
        if not text.isdigit():
            raise DomainError("invalid_money", "Amount must be a decimal with at most two places.")
        minor = int(text) * 100
    return Money(sign * minor, currency)
