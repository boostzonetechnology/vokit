from __future__ import annotations

from enum import StrEnum


class AuditSeverity(StrEnum):
    INFO = "info"
    HIGH = "high"


HIGH_RISK_ACTIONS = frozenset(
    {
        "kyc.override",
        "risk.override",
        "wallet.adjusted",
        "wallet.frozen",
        "commission.reversed",
        "settings.changed",
        "settings.flag_changed",
        "role.invited",
        "user.disabled",
        "agency.suspended",
        "payout.decided",
    }
)

OVERRIDE_ACTIONS = frozenset(
    {
        "kyc.override",
        "risk.override",
        "wallet.adjusted",
        "wallet.frozen",
        "commission.reversed",
        "settings.changed",
        "settings.flag_changed",
        "agency.suspended",
        "payout.decided",
    }
)
