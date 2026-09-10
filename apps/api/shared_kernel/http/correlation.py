from __future__ import annotations

import logging
from collections.abc import Callable
from contextvars import ContextVar

from django.http import HttpRequest, HttpResponse

from shared_kernel.ids import is_uuid, uuid7_str

_HEADER_IN = "HTTP_X_REQUEST_ID"
_HEADER_ALT = "HTTP_X_CORRELATION_ID"
_HEADER_OUT = "X-Request-ID"

_correlation_id: ContextVar[str] = ContextVar("vokit_correlation_id", default="")


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)


def resolve_correlation_id(request: HttpRequest) -> str:
    candidate = request.META.get(_HEADER_IN) or request.META.get(_HEADER_ALT) or ""
    candidate = candidate.strip()
    if candidate and is_uuid(candidate) and len(candidate) <= 64:
        return candidate
    return uuid7_str()


class CorrelationIdMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        token = _correlation_id.set(resolve_correlation_id(request))
        request.correlation_id = _correlation_id.get()
        try:
            response = self.get_response(request)
            response[_HEADER_OUT] = request.correlation_id
            return response
        finally:
            _correlation_id.reset(token)


class CorrelationLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = getattr(record, "correlation_id", None) or get_correlation_id()
        return True
