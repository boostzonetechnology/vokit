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
DEFAULT_SILENCE_TIMEOUT_SECONDS = 20
DEFAULT_MAX_CALL_DURATION_SECONDS = 1800
SILENCE_TIMEOUT_RANGE = (5, 120)
MAX_CALL_DURATION_RANGE = (60, 7200)
SPEAKING_SPEED_RANGE = (0.5, 2.0)
PERSONA_FIELD_MAX = 2000
ROLE_FIELD_MAX = 128
SPEAKING_STYLE_MAX = 64
PRODUCTION_STATUSES = frozenset({AgentStatus.ACTIVE})
TEST_STATUSES = frozenset({AgentStatus.DRAFT, AgentStatus.TESTING, AgentStatus.ACTIVE})
STATUS_ACTORS = frozenset({"agency", "platform", "system"})
RESTRICTIVE_STATUSES = frozenset(
    {AgentStatus.PAUSED, AgentStatus.SUSPENDED, AgentStatus.ARCHIVED, AgentStatus.ERROR}
)
AGENCY_PAUSE_STATUSES = frozenset({AgentStatus.ACTIVE, AgentStatus.TESTING})


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


KNOWLEDGE_FILE_EXTENSIONS = frozenset(
    {"txt", "md", "markdown", "pdf", "docx", "html", "htm", "csv", "json"}
)
MAX_KNOWLEDGE_FILE_BYTES = 5 * 1024 * 1024
MAX_KNOWLEDGE_TEXT_CHARS = 400_000


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
