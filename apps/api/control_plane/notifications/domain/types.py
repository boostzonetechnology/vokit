from __future__ import annotations

from enum import StrEnum


class NotificationChannel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"


class NotificationCategory(StrEnum):
    SECURITY = "security"
    BILLING = "billing"
    KYC = "kyc"
    SUSPENSION = "suspension"
    OPERATIONAL = "operational"
    ANNOUNCEMENT = "announcement"
    INVITATION = "invitation"


class DeliveryStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class PreferenceScope(StrEnum):
    USER = "user"
    AGENCY = "agency"
    CUSTOMER = "customer"


MANDATORY_CATEGORIES = frozenset(
    {
        NotificationCategory.SECURITY,
        NotificationCategory.BILLING,
        NotificationCategory.KYC,
        NotificationCategory.SUSPENSION,
    }
)

EVENT_CATALOG: dict[str, NotificationCategory] = {
    "invitation.agency": NotificationCategory.INVITATION,
    "invitation.customer": NotificationCategory.INVITATION,
    "invitation.platform": NotificationCategory.INVITATION,
    "kyc.submitted": NotificationCategory.KYC,
    "kyc.approved": NotificationCategory.KYC,
    "kyc.rejected": NotificationCategory.KYC,
    "kyc.more_info": NotificationCategory.KYC,
    "payment.success": NotificationCategory.BILLING,
    "payment.failure": NotificationCategory.BILLING,
    "minutes.low": NotificationCategory.BILLING,
    "commission.available": NotificationCategory.BILLING,
    "payout.requested": NotificationCategory.BILLING,
    "payout.paid": NotificationCategory.BILLING,
    "payout.rejected": NotificationCategory.BILLING,
    "agency.suspended": NotificationCategory.SUSPENSION,
    "security.session": NotificationCategory.SECURITY,
    "announcement.platform": NotificationCategory.ANNOUNCEMENT,
}

TEMPLATE_VARIABLES: dict[str, frozenset[str]] = {
    "invitation.agency": frozenset({"email", "role", "token", "accept_url"}),
    "invitation.customer": frozenset({"email", "role", "token", "accept_url"}),
    "invitation.platform": frozenset({"email", "role", "token", "accept_url"}),
    "kyc.submitted": frozenset({"agency_id", "status"}),
    "kyc.approved": frozenset({"agency_id", "status"}),
    "kyc.rejected": frozenset({"agency_id", "status"}),
    "kyc.more_info": frozenset({"agency_id", "status"}),
    "payment.success": frozenset({"invoice_id", "amount"}),
    "payment.failure": frozenset({"invoice_id", "amount"}),
    "minutes.low": frozenset({"customer_id", "remaining"}),
    "commission.available": frozenset({"amount"}),
    "payout.requested": frozenset({"payout_id", "amount"}),
    "payout.paid": frozenset({"payout_id", "amount"}),
    "payout.rejected": frozenset({"payout_id", "amount"}),
    "agency.suspended": frozenset({"agency_id"}),
    "security.session": frozenset({"email"}),
    "announcement.platform": frozenset({"title", "body"}),
}

# Optional CTA for the shared HTML email shell (label, variable key for URL).
EMAIL_CTA: dict[str, tuple[str, str]] = {
    "invitation.agency": ("Accept invitation", "accept_url"),
    "invitation.customer": ("Accept invitation", "accept_url"),
    "invitation.platform": ("Accept invitation", "accept_url"),
}

EMAIL_TITLES: dict[str, str] = {
    "invitation.agency": "You are invited to Vokit",
    "invitation.customer": "You are invited to Vokit",
    "invitation.platform": "You are invited to Vokit",
}

DEFAULT_TEMPLATES: dict[str, dict[str, str]] = {
    "invitation.agency": {
        "subject": "You're invited to a Vokit agency",
        "body": "An agency invitation was issued for {{email}} as {{role}}.",
        "email_body": (
            "You've been invited to join a Vokit agency as {{role}}.\n"
            "Click the button below to set your password and accept the invitation."
        ),
    },
    "invitation.customer": {
        "subject": "You're invited to a Vokit customer",
        "body": "A customer invitation was issued for {{email}} as {{role}}.",
        "email_body": (
            "You've been invited to join a Vokit customer workspace as {{role}}.\n"
            "Click the button below to set your password and accept the invitation."
        ),
    },
    "invitation.platform": {
        "subject": "You're invited to Vokit platform",
        "body": "A platform invitation was issued for {{email}} as {{role}}.",
        "email_body": (
            "You've been invited to the Vokit platform as {{role}}.\n"
            "Click the button below to set your password and accept the invitation."
        ),
    },
    "kyc.submitted": {
        "subject": "Agency KYC submitted",
        "body": "KYC for agency {{agency_id}} is {{status}}.",
        "email_body": "KYC for agency {{agency_id}} is {{status}}.",
    },
    "kyc.approved": {
        "subject": "Agency KYC verified",
        "body": "KYC for agency {{agency_id}} is {{status}}.",
        "email_body": "KYC for agency {{agency_id}} is {{status}}.",
    },
    "kyc.rejected": {
        "subject": "Agency KYC rejected",
        "body": "KYC for agency {{agency_id}} is {{status}}.",
        "email_body": "KYC for agency {{agency_id}} is {{status}}.",
    },
    "kyc.more_info": {
        "subject": "Agency KYC needs more information",
        "body": "KYC for agency {{agency_id}} is {{status}}.",
        "email_body": "KYC for agency {{agency_id}} is {{status}}.",
    },
    "announcement.platform": {
        "subject": "{{title}}",
        "body": "{{body}}",
        "email_body": "{{body}}",
    },
    "agency.suspended": {
        "subject": "Agency access restricted",
        "body": "Agency {{agency_id}} has a suspension or restriction notice.",
        "email_body": "Agency {{agency_id}} has a suspension or restriction notice.",
    },
    "payment.success": {
        "subject": "Payment captured",
        "body": "Payment for invoice {{invoice_id}} succeeded ({{amount}}).",
        "email_body": "Payment for invoice {{invoice_id}} succeeded ({{amount}}).",
    },
    "payment.failure": {
        "subject": "Payment failed",
        "body": "Payment for invoice {{invoice_id}} failed ({{amount}}).",
        "email_body": "Payment for invoice {{invoice_id}} failed ({{amount}}).",
    },
    "minutes.low": {
        "subject": "Low minutes remaining",
        "body": "Customer {{customer_id}} has {{remaining}} minutes remaining.",
        "email_body": "Customer {{customer_id}} has {{remaining}} minutes remaining.",
    },
    "commission.available": {
        "subject": "Commission available",
        "body": "Commission {{amount}} is now available.",
        "email_body": "Commission {{amount}} is now available.",
    },
    "payout.requested": {
        "subject": "Payout requested",
        "body": "Payout {{payout_id}} for {{amount}} was requested.",
        "email_body": "Payout {{payout_id}} for {{amount}} was requested.",
    },
    "payout.paid": {
        "subject": "Payout paid",
        "body": "Payout {{payout_id}} for {{amount}} was marked paid.",
        "email_body": "Payout {{payout_id}} for {{amount}} was marked paid.",
    },
    "payout.rejected": {
        "subject": "Payout rejected",
        "body": "Payout {{payout_id}} for {{amount}} was rejected.",
        "email_body": "Payout {{payout_id}} for {{amount}} was rejected.",
    },
    "security.session": {
        "subject": "Security notice",
        "body": "A security notice was issued for {{email}}.",
        "email_body": "A security notice was issued for {{email}}.",
    },
}

