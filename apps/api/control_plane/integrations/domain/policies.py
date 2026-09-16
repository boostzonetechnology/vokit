from __future__ import annotations

import ipaddress
import json
import uuid
from urllib.parse import urlparse

from control_plane.agents.domain.policies import assert_no_secrets
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


MAX_TOOL_SCHEMA_OVERRIDE_BYTES = 8192
DEFAULT_ACTION_TIMEOUT_SECONDS = 15
ACTION_TIMEOUT_RANGE = (1, 30)

ACTION_SCHEMAS: dict[str, dict[str, object]] = {
    "create_lead": {
        "name": "create_lead",
        "description": "Create a CRM lead.",
        "input_schema": {
            "type": "object",
            "anyOf": [{"required": ["name"]}, {"required": ["email"]}],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "company": {"type": "string"},
            },
        },
        "output_schema": {"type": "object"},
        "timeout_seconds": DEFAULT_ACTION_TIMEOUT_SECONDS,
        "error_behavior": "continue_call",
    },
    "create_contact": {
        "name": "create_contact",
        "description": "Create a CRM contact.",
        "input_schema": {
            "type": "object",
            "anyOf": [{"required": ["name"]}, {"required": ["email"]}],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "company": {"type": "string"},
            },
        },
        "output_schema": {"type": "object"},
        "timeout_seconds": DEFAULT_ACTION_TIMEOUT_SECONDS,
        "error_behavior": "continue_call",
    },
    "update_contact": {
        "name": "update_contact",
        "description": "Update a CRM contact.",
        "input_schema": {
            "type": "object",
            "required": ["contact_id"],
            "properties": {"contact_id": {"type": "string"}},
        },
        "output_schema": {"type": "object"},
        "timeout_seconds": DEFAULT_ACTION_TIMEOUT_SECONDS,
        "error_behavior": "continue_call",
    },
    "book_appointment": {
        "name": "book_appointment",
        "description": "Book an appointment.",
        "input_schema": {
            "type": "object",
            "required": ["starts_at"],
            "properties": {"starts_at": {"type": "string"}},
        },
        "output_schema": {"type": "object"},
        "timeout_seconds": DEFAULT_ACTION_TIMEOUT_SECONDS,
        "error_behavior": "continue_call",
    },
    "lookup_customer": {
        "name": "lookup_customer",
        "description": "Look up a customer.",
        "input_schema": {
            "type": "object",
            "required": ["query"],
            "properties": {"query": {"type": "string"}},
        },
        "output_schema": {"type": "object"},
        "timeout_seconds": DEFAULT_ACTION_TIMEOUT_SECONDS,
        "error_behavior": "continue_call",
    },
    "create_ticket": {
        "name": "create_ticket",
        "description": "Create a support ticket.",
        "input_schema": {
            "type": "object",
            "required": ["subject"],
            "properties": {"subject": {"type": "string"}},
        },
        "output_schema": {"type": "object"},
        "timeout_seconds": DEFAULT_ACTION_TIMEOUT_SECONDS,
        "error_behavior": "continue_call",
    },
    "send_notification": {
        "name": "send_notification",
        "description": "Send a notification.",
        "input_schema": {
            "type": "object",
            "required": ["message"],
            "properties": {"message": {"type": "string"}},
        },
        "output_schema": {"type": "object"},
        "timeout_seconds": DEFAULT_ACTION_TIMEOUT_SECONDS,
        "error_behavior": "continue_call",
    },
    "check_order": {
        "name": "check_order",
        "description": "Check an order.",
        "input_schema": {
            "type": "object",
            "required": ["order_id"],
            "properties": {"order_id": {"type": "string"}},
        },
        "output_schema": {"type": "object"},
        "timeout_seconds": DEFAULT_ACTION_TIMEOUT_SECONDS,
        "error_behavior": "continue_call",
    },
    "create_invoice_context": {
        "name": "create_invoice_context",
        "description": "Create invoice context.",
        "input_schema": {
            "type": "object",
            "required": ["description"],
            "properties": {
                "description": {"type": "string"},
                "amount_minor": {"type": "integer"},
            },
        },
        "output_schema": {"type": "object"},
        "timeout_seconds": DEFAULT_ACTION_TIMEOUT_SECONDS,
        "error_behavior": "continue_call",
    },
    "invoke_webhook": {
        "name": "invoke_webhook",
        "description": "Invoke a configured webhook.",
        "input_schema": {
            "type": "object",
            "properties": {"payload": {"type": "object"}},
        },
        "output_schema": {"type": "object"},
        "timeout_seconds": DEFAULT_ACTION_TIMEOUT_SECONDS,
        "error_behavior": "continue_call",
    },
}


def assert_tool_schema_overrides(raw: object) -> dict[str, dict[str, object]]:
    if raw is None:
        return {}
    if type(raw) is not dict:
        raise DomainError("validation_error", "tool_schema_overrides must be an object.")
    encoded = json.dumps(raw, default=str)
    if len(encoded) > MAX_TOOL_SCHEMA_OVERRIDE_BYTES:
        raise DomainError("validation_error", "tool_schema_overrides is too large.")
    cleaned: dict[str, dict[str, object]] = {}
    for key, spec in raw.items():
        name = str(key).strip()
        if (
            name not in ALLOWED_TOOLS
            or name == "transfer_call"
            or name not in ACTION_SCHEMAS
        ):
            raise DomainError(
                "invalid_tool",
                f"Tool '{name}' is not allowlisted.",
                http_status=422,
            )
        if type(spec) is not dict:
            raise DomainError(
                "validation_error",
                "tool schema override must be an object.",
            )
        input_schema = ACTION_SCHEMAS[name].get("input_schema") or {}
        platform_required = set(
            input_schema.get("required") or []  # type: ignore[union-attr]
        )
        override_input = (
            spec.get("input_schema") if type(spec.get("input_schema")) is dict else {}
        )
        if "required" in override_input:
            override_required = set(str(item) for item in (override_input.get("required") or []))
            if not platform_required.issubset(override_required):
                raise DomainError(
                    "validation_error",
                    "tool schema override cannot remove platform required fields.",
                )
        if "timeout_seconds" in spec and spec.get("timeout_seconds") not in (None, ""):
            try:
                timeout = int(spec.get("timeout_seconds"))
            except (TypeError, ValueError) as exc:
                raise DomainError(
                    "validation_error",
                    "timeout_seconds is invalid.",
                ) from exc
            low, high = ACTION_TIMEOUT_RANGE
            if timeout < low or timeout > high:
                raise DomainError("validation_error", "timeout_seconds is out of range.")
        description = str(spec.get("description") or "")
        assert_no_secrets(description, field="tool schema")
        cleaned[name] = dict(spec)
    return cleaned


def merged_action_schema(action: str, override: dict | None) -> dict[str, object]:
    base = ACTION_SCHEMAS.get(action)
    if base is None:
        raise DomainError("invalid_tool", "Action is not allowlisted.", http_status=422)
    merged = dict(base)
    input_schema = dict(base.get("input_schema") or {})  # type: ignore[arg-type]
    properties = dict(input_schema.get("properties") or {})
    required = list(input_schema.get("required") or [])
    if override:
        override_input = (
            override.get("input_schema")
            if type(override.get("input_schema")) is dict
            else {}
        )
        properties.update(dict(override_input.get("properties") or {}))
        for item in override_input.get("required") or []:
            name = str(item)
            if name not in required:
                required.append(name)
        if override.get("description"):
            merged["description"] = str(override["description"])
        if override.get("timeout_seconds") not in (None, ""):
            merged["timeout_seconds"] = int(override["timeout_seconds"])
    input_schema["properties"] = properties
    if required:
        input_schema["required"] = required
    merged["input_schema"] = input_schema
    return merged


def merged_tool_schemas(
    tools: tuple[str, ...] | list[str],
    overrides: dict[str, dict[str, object]] | None,
) -> dict[str, dict[str, object]]:
    payload: dict[str, dict[str, object]] = {}
    override_map = overrides or {}
    for name in tools:
        if name not in ACTION_SCHEMAS:
            continue
        spec = override_map.get(name)
        payload[name] = merged_action_schema(
            name, spec if type(spec) is dict else None
        )
    return payload


def validate_invoke_arguments(
    action: str, arguments: dict | None, override: dict | None
) -> None:
    data = arguments if isinstance(arguments, dict) else {}
    schema = merged_action_schema(action, override)
    input_schema = schema.get("input_schema") or {}
    required = input_schema.get("required") or []
    for field in required:
        if not str(data.get(str(field)) or "").strip():
            raise DomainError(
                "invalid_arguments",
                f"{field} is required.",
                http_status=422,
            )
    any_of = input_schema.get("anyOf") or []
    if any_of:
        matched = False
        for clause in any_of:
            fields = clause.get("required") or [] if type(clause) is dict else []
            if fields and all(
                str(data.get(str(item)) or "").strip() for item in fields
            ):
                matched = True
                break
        if not matched:
            raise DomainError(
                "invalid_arguments",
                "required fields are missing.",
                http_status=422,
            )
