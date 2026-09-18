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
        "customer.status.changed",
        "customer.minutes.adjusted",
        "mfa.reset",
        "mfa.method_disabled",
        "mfa.recovery_regenerated",
        "agent.status.changed",
        "agent.archived",
        "agent.disabled",
        "agency.commission.changed",
        "agency.capabilities.changed",
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
        "customer.minutes.adjusted",
        "mfa.reset",
        "agent.archived",
        "agent.disabled",
        "agency.commission.changed",
        "agency.capabilities.changed",
    }
)
