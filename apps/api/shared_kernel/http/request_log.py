from __future__ import annotations

import logging
import time
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.http")


class RequestLogMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        started = time.perf_counter()
        response = self.get_response(request)
        latency_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logger,
            "http.request",
            outcome="success" if response.status_code < 500 else "error",
            latency_ms=latency_ms,
            method=request.method,
            path=request.path,
            status=response.status_code,
        )
        return response
