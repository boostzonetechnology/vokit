from __future__ import annotations

from enum import StrEnum


class CallStatus(StrEnum):
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class CallDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class TransferStatus(StrEnum):
    IDLE = "idle"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
