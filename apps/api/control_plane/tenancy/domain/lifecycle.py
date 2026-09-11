from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared_kernel.errors import DomainError


class AgencyStatus(StrEnum):
    INVITED = "invited"
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
            AgencyStatus.INVITED,
            AgencyStatus.PENDING,
            AgencyStatus.RESTRICTED,
            AgencyStatus.UNDER_REVIEW,
            AgencyStatus.SUSPENDED,
        }
    ),
    "restrict": frozenset(
        {
            AgencyStatus.ACTIVE,
            AgencyStatus.UNDER_REVIEW,
            AgencyStatus.PENDING,
            AgencyStatus.INVITED,
        }
    ),
    "review": frozenset(
        {
            AgencyStatus.ACTIVE,
            AgencyStatus.RESTRICTED,
            AgencyStatus.PENDING,
            AgencyStatus.INVITED,
        }
    ),
    "suspend": frozenset(
        {
            AgencyStatus.ACTIVE,
            AgencyStatus.RESTRICTED,
            AgencyStatus.UNDER_REVIEW,
            AgencyStatus.PENDING,
            AgencyStatus.INVITED,
        }
    ),
    "close": frozenset(
        {
            AgencyStatus.ACTIVE,
            AgencyStatus.RESTRICTED,
            AgencyStatus.UNDER_REVIEW,
            AgencyStatus.SUSPENDED,
            AgencyStatus.PENDING,
            AgencyStatus.INVITED,
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


def default_capabilities_for_status(
    status: AgencyStatus,
) -> AgencyCapabilities | None:
    """SRS §24.1 forced-off defaults. True flags mean inherit; False forces off."""
    if status is AgencyStatus.RESTRICTED:
        return AgencyCapabilities(create_customers=False, request_payouts=False)
    if status is AgencyStatus.UNDER_REVIEW:
        return AgencyCapabilities(request_payouts=False)
    if status is AgencyStatus.SUSPENDED:
        return AgencyCapabilities(create_customers=False)
    return None


def merge_capability_gates(
    current: AgencyCapabilities, gates: AgencyCapabilities | None
) -> AgencyCapabilities:
    if gates is None:
        return current
    return AgencyCapabilities(
        create_customers=current.create_customers and gates.create_customers,
        create_agents=current.create_agents and gates.create_agents,
        purchase_numbers=current.purchase_numbers and gates.purchase_numbers,
        request_payouts=current.request_payouts and gates.request_payouts,
        existing_customer_services=(
            current.existing_customer_services and gates.existing_customer_services
        ),
    )


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
