from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.identity.api.auth import parse_optional_uuid, require_principal
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.reporting.domain.periods import parse_window
from control_plane.reporting.infrastructure.container import dashboards
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success

_PLATFORM_DASHBOARD_PERMS = frozenset({"agency.view", "billing.view", "call.view"})
_AGENCY_DASHBOARD_PERMS = frozenset(
    {"customer.view", "agent.view", "call.view", "wallet.view", "team.view", "kyc.view"}
)
_CUSTOMER_DASHBOARD_PERMS = frozenset(
    {"agent.view", "call.view", "billing.pay", "team.view", "recording.view"}
)


def _window(request: Request):
    return parse_window(
        period=str(request.query_params.get("period") or "30d"),
        timezone=str(request.query_params.get("timezone") or "UTC"),
        since=str(request.query_params.get("since") or ""),
        until=str(request.query_params.get("until") or ""),
    )


def _require_any_perm(context, allowed: frozenset[str]) -> None:
    if context.is_super_admin:
        return
    if not (allowed & context.permissions):
        raise DomainError("forbidden", "Not permitted.", http_status=403)


class PlatformDashboardView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.PLATFORM)
        _require_any_perm(context, _PLATFORM_DASHBOARD_PERMS)
        return success(
            dashboards().platform(
                _window(request),
                agency_id=parse_optional_uuid(
                    request.query_params.get("agency_id"), field="agency_id"
                ),
            )
        )


class AgencyDashboardView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.AGENCY)
        if context.membership.tenant_id is None:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        _require_any_perm(context, _AGENCY_DASHBOARD_PERMS)
        return success(dashboards().agency(context.membership.tenant_id, _window(request)))


class CustomerDashboardView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.CUSTOMER)
        membership = context.membership
        if membership.tenant_id is None or membership.customer_id is None:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        _require_any_perm(context, _CUSTOMER_DASHBOARD_PERMS)
        return success(
            dashboards().customer(
                membership.tenant_id,
                membership.customer_id,
                _window(request),
                context.user.id,
            )
        )
