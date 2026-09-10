from __future__ import annotations

from enum import StrEnum


class KycStatus(StrEnum):
    NOT_STARTED = "not_started"
    INCOMPLETE = "incomplete"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    MORE_INFORMATION_REQUIRED = "more_information_required"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class ProviderEventStatus(StrEnum):
    RECEIVED = "received"
    PROCESSED = "processed"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


PROVIDER_STATUS_MAP = {
    "not_started": KycStatus.NOT_STARTED,
    "incomplete": KycStatus.INCOMPLETE,
    "submitted": KycStatus.SUBMITTED,
    "under_review": KycStatus.UNDER_REVIEW,
    "more_information_required": KycStatus.MORE_INFORMATION_REQUIRED,
    "more_info": KycStatus.MORE_INFORMATION_REQUIRED,
    "verified": KycStatus.VERIFIED,
    "rejected": KycStatus.REJECTED,
    "expired": KycStatus.EXPIRED,
    "suspended": KycStatus.SUSPENDED,
}
