"""Bounded vendor HTTP for voice/model catalogs. Never log response bodies or keys."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from shared_kernel.errors import DomainError

_TIMEOUT_SECONDS = 10.0
_DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "VokitPlatform/1.0",
}


def vendor_get(url: str, headers: dict[str, str], *, timeout: float = _TIMEOUT_SECONDS) -> object:
    merged = {**_DEFAULT_HEADERS, **headers}
    request = urllib.request.Request(url, headers=merged, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise DomainError(
            "provider_unavailable",
            _http_error_message(exc.code),
            details={"http_status": int(exc.code)},
            http_status=502,
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DomainError(
            "provider_unavailable",
            "Provider is unreachable or timed out.",
            http_status=502,
        ) from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
        raise DomainError(
            "provider_unavailable",
            "Provider returned an invalid response.",
            http_status=502,
        ) from exc


def _http_error_message(status: int) -> str:
    if status in {401, 403}:
        return "Provider rejected the API key."
    if status == 404:
        return "Provider catalog endpoint was not found."
    if status == 429:
        return "Provider rate limit exceeded. Try again shortly."
    return "Provider is unavailable."
