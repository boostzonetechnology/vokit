from __future__ import annotations

import ipaddress
import uuid
from urllib.parse import urlparse

from control_plane.agents.domain.types import ALLOWED_TOOLS
from control_plane.integrations.domain.types import (
    ACTION_CATEGORIES,
    ALLOWED_EVENT_TYPES,
    PROVIDER_CATEGORY,
    ConnectionStatus,
    ProviderKind,
)
from shared_kernel.errors import DomainError

_BLOCKED_HOSTS = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "metadata",
    }
)


def assert_provider(raw: str) -> ProviderKind:
    try:
        return ProviderKind((raw or "").strip().lower())
    except ValueError as exc:
        raise DomainError("validation_error", "provider is invalid.") from exc


def assert_action(raw: str) -> str:
    name = (raw or "").strip()
    if name not in ALLOWED_TOOLS or name == "transfer_call":
        raise DomainError("invalid_tool", "Action is not allowlisted.", http_status=422)
    return name


def assert_events(raw: list | tuple) -> tuple[str, ...]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in raw:
        name = str(item).strip()
        if not name or name in seen:
            continue
        if name not in ALLOWED_EVENT_TYPES:
            raise DomainError("validation_error", f"event_type '{name}' is not allowed.")
        seen.add(name)
        cleaned.append(name)
    if not cleaned:
        raise DomainError("validation_error", "At least one event type is required.")
    return tuple(cleaned)


def assert_webhook_url(raw: str, *, allow_http: bool) -> str:
    value = (raw or "").strip()
    parsed = urlparse(value)
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"https", "http"}:
        raise DomainError("validation_error", "webhook url must be http(s).")
    if scheme == "http" and not allow_http:
        raise DomainError("validation_error", "webhook url must use https.")
    host = (parsed.hostname or "").strip().lower()
    if not host or parsed.username or parsed.password:
        raise DomainError("validation_error", "webhook url is invalid.")
    if host in _BLOCKED_HOSTS or host.endswith(".localhost") or host.endswith(".internal"):
        raise DomainError("validation_error", "webhook url host is not allowed.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
    ):
        raise DomainError("validation_error", "webhook url host is not allowed.")
    if len(value) > 512:
        raise DomainError("validation_error", "webhook url is too long.")
    return value


def assert_same_customer(
    *,
    connection_customer: uuid.UUID,
    actor_customer: uuid.UUID,
) -> None:
    if connection_customer != actor_customer:
        raise DomainError("not_found", "Resource not found.", http_status=404)


def assert_usable(status: ConnectionStatus) -> None:
    if status is ConnectionStatus.DISABLED:
        raise DomainError(
            "conflict_state",
            "Integration is disabled.",
            http_status=409,
            details={"reason": "disabled"},
        )
    if status is not ConnectionStatus.CONNECTED:
        raise DomainError(
            "conflict_state",
            "Integration is not connected.",
            http_status=409,
            details={"reason": status.value},
        )


def provider_supports_action(provider: ProviderKind, action: str) -> bool:
    categories = ACTION_CATEGORIES.get(action, frozenset())
    return PROVIDER_CATEGORY[provider] in categories


def assert_action_arguments(action: str, arguments: dict) -> dict[str, object]:
    data = arguments if isinstance(arguments, dict) else {}
    required = {
        "create_lead": ("name", "email"),
        "create_contact": ("name", "email"),
        "update_contact": ("contact_id",),
        "book_appointment": ("starts_at",),
        "lookup_customer": ("query",),
        "create_ticket": ("subject",),
        "send_notification": ("message",),
        "check_order": ("order_id",),
        "create_invoice_context": ("description",),
        "invoke_webhook": (),
    }.get(action, ())
    if action in {"create_lead", "create_contact"}:
        if not str(data.get("name") or "").strip() and not str(data.get("email") or "").strip():
            raise DomainError("validation_error", "name or email is required.")
        return {key: data.get(key) for key in ("name", "email", "phone", "company") if key in data}
    for field in required:
        if not str(data.get(field) or "").strip():
            raise DomainError("validation_error", f"{field} is required.")
    allowed = (
        "name",
        "email",
        "phone",
        "company",
        "contact_id",
        "starts_at",
        "query",
        "subject",
        "message",
        "order_id",
        "description",
        "amount_minor",
        "payload",
    )
    return {key: data[key] for key in allowed if key in data}


def sanitized_tool_error(code: str) -> dict[str, object]:
    return {"ok": False, "error": code, "continue_call": True}
