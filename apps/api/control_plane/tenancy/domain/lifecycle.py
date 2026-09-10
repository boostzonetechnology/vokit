from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared_kernel.errors import DomainError


class AgencyStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    UNDER_REVIEW = "under_review"
    SUSPENDED = "suspended"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class AgencyCapabilities:
    create_customers: bool = True
    create_agents: bool = True
    purchase_numbers: bool = True
    request_payouts: bool = True
    existing_customer_services: bool = True


_TRANSITIONS: dict[str, frozenset[AgencyStatus]] = {
    "activate": frozenset(
        {
            AgencyStatus.PENDING,
            AgencyStatus.RESTRICTED,
            AgencyStatus.UNDER_REVIEW,
            AgencyStatus.SUSPENDED,
        }
    ),
    "restrict": frozenset(
        {AgencyStatus.ACTIVE, AgencyStatus.UNDER_REVIEW, AgencyStatus.PENDING}
    ),
    "review": frozenset(
        {AgencyStatus.ACTIVE, AgencyStatus.RESTRICTED, AgencyStatus.PENDING}
    ),
    "suspend": frozenset(
        {
            AgencyStatus.ACTIVE,
            AgencyStatus.RESTRICTED,
            AgencyStatus.UNDER_REVIEW,
            AgencyStatus.PENDING,
        }
    ),
    "close": frozenset(
        {
            AgencyStatus.ACTIVE,
            AgencyStatus.RESTRICTED,
            AgencyStatus.UNDER_REVIEW,
            AgencyStatus.SUSPENDED,
            AgencyStatus.PENDING,
        }
    ),
}

_ACTION_STATUS = {
    "activate": AgencyStatus.ACTIVE,
    "restrict": AgencyStatus.RESTRICTED,
    "review": AgencyStatus.UNDER_REVIEW,
    "suspend": AgencyStatus.SUSPENDED,
    "close": AgencyStatus.CLOSED,
}


def apply_agency_status_action(
    current: AgencyStatus, action: str
) -> AgencyStatus:
    normalized = (action or "").strip().lower()
    if normalized == "reactivate":
        normalized = "activate"
    allowed = _TRANSITIONS.get(normalized)
    if allowed is None:
        raise DomainError("validation_error", "Unknown agency status action.")
    if current is AgencyStatus.CLOSED:
        raise DomainError(
            "agency_closed",
            "A closed agency cannot change status.",
            http_status=409,
        )
    if current not in allowed:
        raise DomainError(
            "invalid_agency_status",
            "Agency status transition is not allowed.",
            http_status=409,
        )
    return _ACTION_STATUS[normalized]


def assert_agency_may_create_customer(
    status: AgencyStatus,
    capabilities: AgencyCapabilities,
    *,
    privileged: bool,
) -> None:
    if status in {AgencyStatus.SUSPENDED, AgencyStatus.CLOSED}:
        raise DomainError(
            "agency_cannot_create_customer",
            "Customer creation is not available.",
            http_status=409,
        )
    if not capabilities.create_customers:
        raise DomainError(
            "agency_cannot_create_customer",
            "Customer creation is not available.",
            http_status=409,
        )
    if privileged:
        return
    if status is not AgencyStatus.ACTIVE:
        raise DomainError(
            "agency_cannot_create_customer",
            "Customer creation is not available.",
            http_status=409,
        )


def assert_agency_may_purchase_numbers(
    status: AgencyStatus,
    capabilities: AgencyCapabilities,
    *,
    privileged: bool,
) -> None:
    if status in {AgencyStatus.SUSPENDED, AgencyStatus.CLOSED}:
        raise DomainError(
            "number_purchase_blocked",
            "Number purchase is not available.",
            http_status=409,
        )
    if not capabilities.purchase_numbers:
        raise DomainError(
            "number_purchase_blocked",
            "Number purchase is not available.",
            http_status=409,
        )
    if privileged:
        return
    if status is not AgencyStatus.ACTIVE:
        raise DomainError(
            "number_purchase_blocked",
            "Number purchase is not available.",
            http_status=409,
        )


def assert_agency_may_mutate_customer(
    status: AgencyStatus,
    capabilities: AgencyCapabilities,
    *,
    privileged: bool,
) -> None:
    if privileged:
        if status is AgencyStatus.CLOSED:
            raise DomainError(
                "agency_closed",
                "A closed agency cannot change customers.",
                http_status=409,
            )
        return
    if status is AgencyStatus.CLOSED:
        raise DomainError(
            "agency_closed",
            "A closed agency cannot change customers.",
            http_status=409,
        )
    if not capabilities.existing_customer_services:
        raise DomainError(
            "customer_services_disabled",
            "Customer services are disabled.",
            http_status=409,
        )
