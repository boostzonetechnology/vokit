from __future__ import annotations

from django.conf import settings
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from shared_kernel.http.envelope import failure, success


@api_view(["GET"])
@permission_classes([AllowAny])
def liveness(request: Request) -> Response:
    return success({"status": "ok", "service": "api"})


@api_view(["GET"])
@permission_classes([AllowAny])
def readiness(request: Request) -> Response:
    checks: dict[str, str] = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "failed"
        return failure(
            "not_ready",
            "Service is not ready.",
            status=503,
            details={"checks": checks},
        )
    if getattr(settings, "VOKIT_PRODUCTION_HARDENING", False):
        telephony = str(getattr(settings, "VOKIT_INTERNAL_TELEPHONY_TOKEN", "") or "")
        recording = str(getattr(settings, "VOKIT_INTERNAL_RECORDING_TOKEN", "") or "")
        checks["telephony_token"] = "ok" if telephony else "failed"
        checks["recording_token"] = "ok" if recording else "failed"
        distinct = "ok" if telephony and recording and telephony != recording else "failed"
        checks["token_separation"] = distinct
        runtime = str(getattr(settings, "TENANT_RUNTIME", "") or "")
        checks["tenant_runtime"] = "ok" if runtime == "mysql" else "failed"
        tls = bool(getattr(settings, "TENANT_TLS_REQUIRED", False))
        checks["tenant_tls"] = "ok" if tls else "failed"
        if any(value == "failed" for value in checks.values()):
            return failure(
                "not_ready",
                "Service is not ready.",
                status=503,
                details={"checks": checks},
            )
    return success({"status": "ready", "service": "api", "checks": checks})
