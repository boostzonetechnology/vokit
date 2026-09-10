from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.identity.api.auth import parse_optional_uuid, parse_uuid, require_principal
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.integrations.infrastructure.container import integration_control
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success


def _require_platform_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.PLATFORM)
    if permission not in context.permissions:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _require_agency_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.AGENCY)
    if permission not in context.permissions or context.membership.tenant_id is None:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _require_customer_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.CUSTOMER)
    if permission not in context.permissions or context.membership.customer_id is None:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _bool_field(data: dict, name: str) -> bool:
    raw = data.get(name)
    if type(raw) is not bool:
        raise DomainError("validation_error", f"{name} must be a boolean.")
    return raw


class PlatformProviderCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "integrations.review")
        return success(integration_control().providers())


class PlatformConnectionCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "integrations.review")
        return success(
            integration_control().list_connections(
                tenant_id=parse_optional_uuid(
                    request.query_params.get("agency_id"), field="agency_id"
                ),
                customer_id=parse_optional_uuid(
                    request.query_params.get("customer_id"), field="customer_id"
                ),
                actor_customer_id=None,
                privileged=True,
            )
        )


class PlatformConnectionDisableView(CsrfAPIView):
    def post(self, request: Request, connection_id: str) -> Response:
        _require_platform_perm(request, "integrations.review")
        return success(
            integration_control().disable(
                connection_id=parse_uuid(connection_id, field="connection_id")
            )
        )


class AgencyConnectionCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = _require_agency_perm(request, "integrations.manage")
        customer_id = parse_uuid(
            request.query_params.get("customer_id"), field="customer_id"
        )
        return success(
            integration_control().list_connections(
                tenant_id=context.membership.tenant_id,
                customer_id=customer_id,
                actor_customer_id=None,
                privileged=True,
            )
        )

    def post(self, request: Request) -> Response:
        context = _require_agency_perm(request, "integrations.manage")
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            integration_control().connect(
                tenant_id=context.membership.tenant_id,
                customer_id=parse_uuid(data.get("customer_id"), field="customer_id"),
                provider=str(data.get("provider") or ""),
                credential=str(data.get("credential") or ""),
                display_name=str(data.get("display_name") or ""),
                actor_customer_id=None,
                privileged=True,
            ),
            status=201,
        )


class AgencyConnectionSettingsView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = _require_agency_perm(request, "integrations.manage")
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            integration_control().set_self_service(
                tenant_id=context.membership.tenant_id,
                customer_id=parse_uuid(data.get("customer_id"), field="customer_id"),
                enabled=_bool_field(data, "self_service"),
            )
        )


class AgencyConnectionTestView(CsrfAPIView):
    def post(self, request: Request, connection_id: str) -> Response:
        context = _require_agency_perm(request, "integrations.manage")
        return success(
            integration_control().test_connection(
                tenant_id=context.membership.tenant_id,
                connection_id=parse_uuid(connection_id, field="connection_id"),
                actor_customer_id=None,
                privileged=True,
            )
        )


class AgencyConnectionDisconnectView(CsrfAPIView):
    def post(self, request: Request, connection_id: str) -> Response:
        context = _require_agency_perm(request, "integrations.manage")
        return success(
            integration_control().disconnect(
                tenant_id=context.membership.tenant_id,
                connection_id=parse_uuid(connection_id, field="connection_id"),
                actor_customer_id=None,
                privileged=True,
            )
        )


class AgencyWebhookCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = _require_agency_perm(request, "webhooks.manage")
        customer_id = parse_uuid(
            request.query_params.get("customer_id"), field="customer_id"
        )
        return success(
            integration_control().list_endpoints(
                tenant_id=context.membership.tenant_id,
                customer_id=customer_id,
                actor_customer_id=None,
                privileged=True,
            )
        )

    def post(self, request: Request) -> Response:
        context = _require_agency_perm(request, "webhooks.manage")
        data = request.data if isinstance(request.data, dict) else {}
        events = data.get("events") if isinstance(data.get("events"), list) else []
        return success(
            integration_control().create_endpoint(
                tenant_id=context.membership.tenant_id,
                customer_id=parse_uuid(data.get("customer_id"), field="customer_id"),
                url=str(data.get("url") or ""),
                events=events,
                actor_customer_id=None,
                privileged=True,
            ),
            status=201,
        )


class AgencyWebhookRotateView(CsrfAPIView):
    def post(self, request: Request, endpoint_id: str) -> Response:
        context = _require_agency_perm(request, "webhooks.manage")
        return success(
            integration_control().rotate_secret(
                tenant_id=context.membership.tenant_id,
                endpoint_id=parse_uuid(endpoint_id, field="endpoint_id"),
                actor_customer_id=None,
                privileged=True,
            )
        )


class AgencyWebhookDeliveryCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = _require_agency_perm(request, "webhooks.manage")
        return success(
            integration_control().list_deliveries(
                tenant_id=context.membership.tenant_id,
                customer_id=parse_uuid(
                    request.query_params.get("customer_id"), field="customer_id"
                ),
                actor_customer_id=None,
                privileged=True,
            )
        )


class AgencyWebhookReplayView(CsrfAPIView):
    def post(self, request: Request, delivery_id: str) -> Response:
        context = _require_agency_perm(request, "webhooks.manage")
        return success(
            integration_control().replay(
                tenant_id=context.membership.tenant_id,
                delivery_id=parse_uuid(delivery_id, field="delivery_id"),
                actor_customer_id=None,
                privileged=True,
            )
        )


class CustomerConnectionCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = _require_customer_perm(request, "integrations.view")
        return success(
            integration_control().list_connections(
                tenant_id=context.membership.tenant_id,
                customer_id=context.membership.customer_id,
                actor_customer_id=context.membership.customer_id,
                privileged=False,
            )
        )

    def post(self, request: Request) -> Response:
        context = _require_customer_perm(request, "integrations.connect")
        data = request.data if isinstance(request.data, dict) else {}
        return success(
            integration_control().connect(
                tenant_id=context.membership.tenant_id,
                customer_id=context.membership.customer_id,
                provider=str(data.get("provider") or ""),
                credential=str(data.get("credential") or ""),
                display_name=str(data.get("display_name") or ""),
                actor_customer_id=context.membership.customer_id,
                privileged=False,
            ),
            status=201,
        )


class CustomerConnectionTestView(CsrfAPIView):
    def post(self, request: Request, connection_id: str) -> Response:
        context = _require_customer_perm(request, "integrations.view")
        return success(
            integration_control().test_connection(
                tenant_id=context.membership.tenant_id,
                connection_id=parse_uuid(connection_id, field="connection_id"),
                actor_customer_id=context.membership.customer_id,
                privileged=False,
            )
        )
