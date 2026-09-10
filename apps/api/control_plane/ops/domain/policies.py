from __future__ import annotations

import re

from shared_kernel.errors import DomainError

ATTESTATION_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LIVE_FLAG_NAMES = ("calling_live", "billing_live", "recordings_live")


def feature_flag_disabled(flag: str) -> DomainError:
    return DomainError(
        "feature_flag_disabled",
        f"{flag} is not enabled.",
        http_status=503,
    )


def parse_attestation(raw: str) -> str | None:
    value = (raw or "").strip()
    if ATTESTATION_DATE.fullmatch(value):
        return value
    return None
