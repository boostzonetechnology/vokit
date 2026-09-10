from __future__ import annotations

from typing import Any

from rest_framework.response import Response

from shared_kernel.http.correlation import get_correlation_id


def success(data: Any, *, status: int = 200, page: dict[str, Any] | None = None) -> Response:
    meta: dict[str, Any] = {"request_id": get_correlation_id()}
    if page is not None:
        meta["page"] = page
    return Response({"data": data, "meta": meta}, status=status)


def failure(
    code: str,
    message: str,
    *,
    status: int = 400,
    details: dict[str, Any] | None = None,
) -> Response:
    return Response(
        {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
            "meta": {"request_id": get_correlation_id()},
        },
        status=status,
    )
