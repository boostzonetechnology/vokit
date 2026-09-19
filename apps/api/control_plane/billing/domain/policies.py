from __future__ import annotations

import uuid

from control_plane.billing.domain.types import (
    COMMISSIONABLE_BY_DEFAULT,
    InvoiceStatus,
    LineKind,
)
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


def assigned_plan_is_payment_due(subscription_id: uuid.UUID | None, invoices) -> bool:
    """True only when the assigned plan invoice is OPEN. Other open invoices do not count."""
    if subscription_id is None:
        return False
    for invoice in invoices:
        if invoice.subscription_id != subscription_id:
            continue
        if invoice.status is not InvoiceStatus.OPEN:
            continue
        if any(line.kind is LineKind.SUBSCRIPTION for line in invoice.lines):
            return True
    return False


def invoice_not_found() -> DomainError:
    return DomainError("not_found", "Resource not found.", http_status=404)


def payment_amount_mismatch() -> DomainError:
    return DomainError(
        "payment_amount_mismatch",
        "Captured amount does not match the open invoice.",
        http_status=409,
    )
