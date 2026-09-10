from __future__ import annotations

from enum import StrEnum

from control_plane.risk.domain.types import AgentStatus

ALLOWED_TOOLS = frozenset(
    {
        "create_lead",
        "create_contact",
        "update_contact",
        "book_appointment",
        "lookup_customer",
        "create_ticket",
        "send_notification",
        "check_order",
        "create_invoice_context",
        "transfer_call",
        "invoke_webhook",
    }
)

AGENT_TYPES = frozenset(
    {
        "receptionist",
        "appointment",
        "support",
        "sales",
        "real_estate",
        "medical_receptionist",
        "restaurant",
        "hotel",
        "ecommerce",
        "dispatch",
        "after_hours",
        "faq",
        "custom",
    }
)

FALLBACKS = frozenset({"message", "transfer", "hangup"})
PRODUCTION_STATUSES = frozenset({AgentStatus.ACTIVE})
TEST_STATUSES = frozenset({AgentStatus.DRAFT, AgentStatus.TESTING, AgentStatus.ACTIVE})


class TemplateVisibility(StrEnum):
    GLOBAL = "global"
    SELECTED = "selected"
    INTERNAL = "internal"


class TemplateStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class KnowledgeScope(StrEnum):
    GLOBAL = "global"
    AGENCY = "agency"
    CUSTOMER = "customer"
    AGENT = "agent"


class KnowledgeKind(StrEnum):
    TEXT = "text"
    QA = "qa"
    FILE = "file"
    URL = "url"


class KnowledgeStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    STALE = "stale"


class TestSessionKind(StrEnum):
    TEST = "test"
    TRAINING = "training"


class TestSessionStatus(StrEnum):
    OPEN = "open"
    ENDED = "ended"
