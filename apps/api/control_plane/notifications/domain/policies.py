from __future__ import annotations

import html
import re

from control_plane.notifications.domain.types import (
    EVENT_CATALOG,
    MANDATORY_CATEGORIES,
    TEMPLATE_VARIABLES,
    NotificationCategory,
)
from shared_kernel.errors import DomainError

_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def assert_event_type(raw: str) -> str:
    name = (raw or "").strip()
    if name not in EVENT_CATALOG:
        raise DomainError("validation_error", "event_type is invalid.")
    return name


def category_for(event_type: str) -> NotificationCategory:
    return EVENT_CATALOG[assert_event_type(event_type)]


def is_mandatory(event_type: str) -> bool:
    return category_for(event_type) in MANDATORY_CATEGORIES


def assert_preference_allowed(event_type: str, *, email: bool, in_app: bool) -> None:
    if is_mandatory(event_type) and (not email or not in_app):
        raise DomainError(
            "mandatory_notice",
            "Mandatory notices cannot be disabled.",
            http_status=409,
        )


def render_template(template: str, variables: dict[str, str], event_type: str) -> str:
    allowed = TEMPLATE_VARIABLES.get(event_type, frozenset())
    unknown = set(variables) - allowed
    extra = _PLACEHOLDER.findall(template)
    if unknown:
        raise DomainError("validation_error", "Unknown template variable.")
    for name in extra:
        if name not in allowed:
            raise DomainError("validation_error", f"Template variable '{name}' is not allowed.")

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return html.escape(str(variables.get(key, "")), quote=True)

    return _PLACEHOLDER.sub(_replace, template)


def assert_template_body(body: str, event_type: str) -> str:
    text = (body or "").strip()
    if not text:
        raise DomainError("validation_error", "template body is required.")
    render_template(text, {name: "" for name in TEMPLATE_VARIABLES[event_type]}, event_type)
    return text[:4000]
