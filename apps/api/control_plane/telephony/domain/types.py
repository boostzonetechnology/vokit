from __future__ import annotations

from enum import StrEnum

RESERVATION_SECONDS = 600


class NumberStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    PENDING = "pending"
    ASSIGNED = "assigned"
    FAILED = "failed"
    RELEASING = "releasing"
    RELEASED = "released"


class ReservationStatus(StrEnum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AssignmentStatus(StrEnum):
    ASSIGNED = "assigned"
    RELEASED = "released"


class NumberCapability(StrEnum):
    VOICE = "voice"
    SMS = "sms"
    MMS = "mms"
