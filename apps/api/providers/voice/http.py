"""Bounded vendor HTTP for TTS voice catalogs. Never log response bodies or keys."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from shared_kernel.errors import DomainError

_TIMEOUT_SECONDS = 5.0


def vendor_get(url: str, headers: dict[str, str], *, timeout: float = _TIMEOUT_SECONDS) -> object:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise DomainError(
            "provider_unavailable",
            "Voice provider is unavailable.",
            http_status=502,
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DomainError(
            "provider_unavailable",
            "Voice provider is unavailable.",
            http_status=502,
        ) from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
        raise DomainError(
            "provider_unavailable",
            "Voice provider is unavailable.",
            http_status=502,
        ) from exc
