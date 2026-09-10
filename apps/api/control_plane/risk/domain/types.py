from __future__ import annotations

from enum import StrEnum
from uuid import UUID

SYSTEM_ACTOR_ID = UUID("00000000-0000-7000-8000-000000000001")


class RiskStatus(StrEnum):
    NORMAL = "normal"
    PAYMENT_REVIEW_REQUIRED = "payment_review_required"
    VERIFICATION_REQUIRED = "verification_required"
    VERIFICATION_SUBMITTED = "verification_submitted"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    CHARGEBACK_FROZEN = "chargeback_frozen"
    PERMANENTLY_BANNED = "permanently_banned"


class VerificationStatus(StrEnum):
    INCOMPLETE = "incomplete"
    SUBMITTED = "submitted"
    REJECTED_MASK = "rejected_mask"
    MANUAL_REVIEW = "manual_review"


class AgentStatus(StrEnum):
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    ERROR = "error"
    ARCHIVED = "archived"


COMMERCIALLY_BLOCKED = frozenset(
    {
        RiskStatus.CHARGEBACK_FROZEN,
        RiskStatus.PERMANENTLY_BANNED,
        RiskStatus.SUSPENDED,
    }
)

CHARGEBACK_STATUSES = frozenset(
    {
        "chargeback",
        "chargeback.confirmed",
        "dispute.lost",
        "charge.dispute.funds_withdrawn",
        "charge.dispute.closed.lost",
    }
)

RISK_FLAG_STATUSES = frozenset(
    {
        "risk_flagged",
        "payment_risk.elevated",
        "radar.early_fraud_warning",
    }
)
