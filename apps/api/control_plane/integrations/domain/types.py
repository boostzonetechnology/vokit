from __future__ import annotations

from enum import StrEnum


class ProviderKind(StrEnum):
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    ZOHO = "zoho"
    QUICKBOOKS = "quickbooks"
    N8N = "n8n"
    ZAPIER = "zapier"
    MAKE = "make"
    GENERIC_WEBHOOK = "generic_webhook"


class ProviderCategory(StrEnum):
    CRM = "crm"
    ACCOUNTING = "accounting"
    AUTOMATION = "automation"


class ConnectionStatus(StrEnum):
    PENDING = "pending"
    CONNECTED = "connected"
    DISABLED = "disabled"
    REVOKED = "revoked"


class EndpointStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD = "dead"


PROVIDER_CATEGORY: dict[ProviderKind, ProviderCategory] = {
    ProviderKind.HUBSPOT: ProviderCategory.CRM,
    ProviderKind.SALESFORCE: ProviderCategory.CRM,
    ProviderKind.ZOHO: ProviderCategory.CRM,
    ProviderKind.QUICKBOOKS: ProviderCategory.ACCOUNTING,
    ProviderKind.N8N: ProviderCategory.AUTOMATION,
    ProviderKind.ZAPIER: ProviderCategory.AUTOMATION,
    ProviderKind.MAKE: ProviderCategory.AUTOMATION,
    ProviderKind.GENERIC_WEBHOOK: ProviderCategory.AUTOMATION,
}

CRM_ACTIONS = frozenset(
    {
        "create_lead",
        "create_contact",
        "update_contact",
        "lookup_customer",
        "create_ticket",
        "book_appointment",
    }
)
ACCOUNTING_ACTIONS = frozenset({"create_invoice_context", "check_order"})
AUTOMATION_ACTIONS = frozenset({"invoke_webhook", "send_notification"})

ACTION_CATEGORIES: dict[str, frozenset[ProviderCategory]] = {
    "create_lead": frozenset({ProviderCategory.CRM}),
    "create_contact": frozenset({ProviderCategory.CRM}),
    "update_contact": frozenset({ProviderCategory.CRM}),
    "book_appointment": frozenset({ProviderCategory.CRM}),
    "lookup_customer": frozenset({ProviderCategory.CRM}),
    "create_ticket": frozenset({ProviderCategory.CRM}),
    "send_notification": frozenset({ProviderCategory.AUTOMATION, ProviderCategory.CRM}),
    "check_order": frozenset({ProviderCategory.ACCOUNTING, ProviderCategory.CRM}),
    "create_invoice_context": frozenset({ProviderCategory.ACCOUNTING}),
    "invoke_webhook": frozenset({ProviderCategory.AUTOMATION}),
}

ALLOWED_EVENT_TYPES = frozenset(
    {
        "agency.created",
        "agency.status.changed",
        "customer.created",
        "customer.status.changed",
        "invoice.created",
        "invoice.paid",
        "payment.failed",
        "commission.created",
        "commission.available",
        "commission.reversed",
        "payout.requested",
        "payout.status.changed",
        "payout.paid",
        "agent.created",
        "agent.published",
        "agent.status.changed",
        "call.started",
        "call.answered",
        "call.completed",
        "call.transcript.ready",
        "call.summary.ready",
        "agent.action.started",
        "agent.action.completed",
        "agent.action.failed",
        "knowledge.updated",
        "phone_number.purchased",
        "phone_number.released",
        "integration.failed",
    }
)

MAX_WEBHOOK_ATTEMPTS = 5
