from __future__ import annotations

from enum import StrEnum


class PrincipalType(StrEnum):
    PLATFORM = "platform"
    AGENCY = "agency"
    CUSTOMER = "customer"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class InvitationStatus(StrEnum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class MembershipStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    DISABLED = "disabled"
