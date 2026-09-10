from __future__ import annotations

from control_plane.billing.domain.types import COMMISSIONABLE_BY_DEFAULT, LineKind
from shared_kernel.errors import DomainError
from shared_kernel.money import Money


def assert_plan_version_mutable(*, used: bool) -> None:
    if used:
        raise DomainError(
            "plan_version_immutable",
            "Plan versions cannot change after a subscription uses them.",
            http_status=409,
        )


def assert_positive_minutes(value: int, *, field: str) -> None:
    if type(value) is not int or value < 0:
        raise DomainError("validation_error", f"{field} must be a non-negative integer.")


def assert_grace_seconds(value: int) -> None:
    if type(value) is not int or value < 0:
        raise DomainError("validation_error", "grace_seconds must be a non-negative integer.")


def line_is_commissionable(kind: LineKind) -> bool:
    return kind in COMMISSIONABLE_BY_DEFAULT


def assert_invoice_total(lines: tuple[Money, ...], total: Money) -> None:
    acc = Money(0, total.currency)
    for amount in lines:
        acc = acc + amount
    if acc.minor_units != total.minor_units:
        raise DomainError(
            "invalid_invoice_total",
            "Invoice total must equal the sum of line amounts.",
        )


def invoice_not_found() -> DomainError:
    return DomainError("not_found", "Resource not found.", http_status=404)


def payment_amount_mismatch() -> DomainError:
    return DomainError(
        "payment_amount_mismatch",
        "Captured amount does not match the open invoice.",
        http_status=409,
    )
