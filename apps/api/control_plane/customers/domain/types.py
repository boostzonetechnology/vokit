from __future__ import annotations

from enum import StrEnum

from shared_kernel.errors import DomainError


class CustomerStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


def apply_customer_status_action(
    current: CustomerStatus,
    action: str,
    *,
    privileged: bool,
) -> CustomerStatus:
    normalized = (action or "").strip().lower()
    if current is CustomerStatus.CLOSED:
        raise DomainError(
            "customer_closed",
            "A closed customer cannot change status.",
            http_status=409,
        )
    if normalized == "suspend":
        if current is not CustomerStatus.ACTIVE:
            raise DomainError(
                "invalid_customer_status",
                "Customer status transition is not allowed.",
                http_status=409,
            )
        return CustomerStatus.SUSPENDED
    if normalized in {"activate", "reactivate"}:
        if current is CustomerStatus.SUSPENDED:
            return CustomerStatus.ACTIVE
        if current is CustomerStatus.INVITED and privileged:
            return CustomerStatus.ACTIVE
        raise DomainError(
            "invalid_customer_status",
            "Customer status transition is not allowed.",
            http_status=409,
        )
    if normalized == "close":
        if not privileged:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        return CustomerStatus.CLOSED
    raise DomainError("validation_error", "Unknown customer status action.")
