from __future__ import annotations

from typing import Any

from django.http import HttpRequest, JsonResponse
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied
from rest_framework.views import exception_handler

from shared_kernel.errors import DomainError
from shared_kernel.http.correlation import get_correlation_id
from shared_kernel.http.envelope import failure


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Any:
    if isinstance(exc, DomainError):
        return failure(exc.code, exc.message, status=exc.http_status, details=exc.details)
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        return failure("unauthenticated", "Authentication required.", status=401)
    if isinstance(exc, PermissionDenied):
        return failure("forbidden", "Not permitted.", status=403)
    response = exception_handler(exc, context)
    if response is None:
        return failure("internal_error", "An unexpected error occurred.", status=500)
    return failure(
        "request_error",
        "The request could not be processed.",
        status=response.status_code,
        details={},
    )


def csrf_failure(request: HttpRequest, reason: str = "") -> JsonResponse:
    return JsonResponse(
        {
            "error": {
                "code": "csrf_denied",
                "message": "CSRF validation failed.",
                "details": {},
            },
            "meta": {"request_id": get_correlation_id()},
        },
        status=403,
    )
