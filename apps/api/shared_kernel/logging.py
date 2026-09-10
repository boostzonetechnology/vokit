from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from shared_kernel.http.correlation import get_correlation_id

FORBIDDEN_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "authorization",
        "cookie",
        "dsn",
        "pan",
        "cvv",
        "cvc",
        "transcript",
        "audio",
        "proof",
        "refresh_token",
        "api_key",
        "signing_secret",
        "passwd",
        "credential",
    }
)


def _redact(key: str, value: Any) -> Any:
    lowered = key.lower()
    if lowered in FORBIDDEN_KEYS or any(part in lowered for part in FORBIDDEN_KEYS):
        return "[redacted]"
    return value


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": record.levelname.lower(),
            "service": getattr(record, "service", "api"),
            "module": record.name,
            "event": getattr(record, "event", record.getMessage()),
            "correlation_id": getattr(record, "correlation_id", None) or get_correlation_id(),
        }
        extra = getattr(record, "vokit", None)
        if isinstance(extra, dict):
            for key, value in extra.items():
                payload[key] = _redact(str(key), value)
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
        return json.dumps(payload, default=str)


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    severity: str = "info",
    outcome: str | None = None,
    latency_ms: int | None = None,
    **fields: Any,
) -> None:
    safe = {key: _redact(key, value) for key, value in fields.items()}
    if outcome is not None:
        safe["outcome"] = outcome
    if latency_ms is not None:
        safe["latency_ms"] = latency_ms
    level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(level, event, extra={"event": event, "vokit": safe})
