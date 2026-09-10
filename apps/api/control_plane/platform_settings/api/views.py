from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.identity.api.auth import parse_uuid, require_principal
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.platform_settings.infrastructure.container import platform_settings
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success


def _require_platform_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.PLATFORM)
    if permission not in context.permissions:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _client_ip(request: Request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.META.get("REMOTE_ADDR") or "")[:64]


class PlatformSettingsView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "settings.manage")
        return success(platform_settings().snapshot())

    def patch(self, request: Request) -> Response:
        context = _require_platform_perm(request, "settings.manage")
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            platform_settings().update(
                key=str(data.get("key") or ""),
                value=data.get("value"),
                reason=str(data.get("reason") or ""),
                actor_id=context.user.id,
                actor_role=context.membership.role,
                ip=_client_ip(request),
                user_agent=str(request.META.get("HTTP_USER_AGENT") or "")[:255],
            )
        )


class PlatformAgencyFlagView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = _require_platform_perm(request, "settings.manage")
        data = request.data if isinstance(request.data, dict) else {}
        enabled = data.get("enabled")
        if type(enabled) is not bool:
            raise DomainError("validation_error", "enabled must be a boolean.")
        return success(
            platform_settings().set_agency_flag(
                tenant_id=parse_uuid(data.get("agency_id"), field="agency_id"),
                flag=str(data.get("flag") or ""),
                enabled=enabled,
                reason=str(data.get("reason") or ""),
                actor_id=context.user.id,
                actor_role=context.membership.role,
                ip=_client_ip(request),
                user_agent=str(request.META.get("HTTP_USER_AGENT") or "")[:255],
            )
        )
