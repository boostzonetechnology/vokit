from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.identity.api.auth import parse_uuid, require_principal
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.application.create_agency import CreateAgencyCommand
from control_plane.tenancy.application.ports import TenantRecord
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities
from control_plane.tenancy.infrastructure.container import (
    change_agency_capabilities,
    change_agency_status,
    create_agency,
    set_commission_rate,
    tenant_repo,
    update_agency_profile,
)
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page


def _require_platform_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.PLATFORM)
    if permission not in context.permissions:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _capabilities_from(data: dict) -> AgencyCapabilities:
    caps = data.get("capabilities") or {}
    base = AgencyCapabilities()
    return AgencyCapabilities(
        create_customers=bool(caps.get("create_customers", base.create_customers)),
        create_agents=bool(caps.get("create_agents", base.create_agents)),
        purchase_numbers=bool(caps.get("purchase_numbers", base.purchase_numbers)),
        request_payouts=bool(caps.get("request_payouts", base.request_payouts)),
        existing_customer_services=bool(
            caps.get("existing_customer_services", base.existing_customer_services)
        ),
    )


def _agency_payload(tenant: TenantRecord) -> dict[str, object]:
    caps = tenant.capabilities
    return {
        "id": str(tenant.id),
        "display_name": tenant.display_name,
        "legal_name": tenant.legal_name,
        "tenant_status": tenant.status.value,
        "status": tenant.agency_status.value,
        "currency": tenant.currency,
        "commission_rate_bps": tenant.commission_rate_bps,
        "rate_effective_at": (
            tenant.rate_effective_at.isoformat() if tenant.rate_effective_at else None
        ),
        "capabilities": {
            "create_customers": caps.create_customers,
            "create_agents": caps.create_agents,
            "purchase_numbers": caps.purchase_numbers,
            "request_payouts": caps.request_payouts,
            "existing_customer_services": caps.existing_customer_services,
        },
    }


class AgencyCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "agencies.view")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows = tenant_repo().list()
        sliced, page = page_slice(rows, offset, limit)
        return success([_agency_payload(row) for row in sliced], page=page)

    def post(self, request: Request) -> Response:
        context = _require_platform_perm(request, "agencies.create")
        if "database" in request.data:
            raise DomainError(
                "validation_error",
                "database must not be supplied; the server allocates tenant databases.",
                http_status=400,
            )
        created = create_agency().execute(
            CreateAgencyCommand(
                display_name=str(request.data.get("display_name") or ""),
                legal_name=str(request.data.get("legal_name") or ""),
                owner_email=str(request.data.get("owner_email") or ""),
                actor=context.membership,
                commission_rate_bps=int(request.data.get("commission_rate_bps") or 0),
                currency=str(request.data.get("currency") or "USD"),
                capabilities=_capabilities_from(request.data),
                tenant_id=None,
            )
        )
        payload = _agency_payload(created.tenant)
        if created.invitation_token:
            payload["owner_invitation_token"] = created.invitation_token
        return success(payload, status=201)


class AgencyDetailView(CsrfAPIView):
    def get(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "agencies.view")
        tenant = tenant_repo().get(parse_uuid(agency_id, field="agency_id"))
        if tenant is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return success(_agency_payload(tenant))

    def patch(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "agencies.manage")
        tenant = update_agency_profile().execute(
            parse_uuid(agency_id, field="agency_id"),
            display_name=request.data.get("display_name"),
            legal_name=request.data.get("legal_name"),
        )
        return success(_agency_payload(tenant))


class AgencyStatusView(CsrfAPIView):
    def post(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "agencies.manage")
        tenant = change_agency_status().execute(
            parse_uuid(agency_id, field="agency_id"),
            str(request.data.get("action") or ""),
        )
        return success(_agency_payload(tenant))


class AgencyCapabilitiesView(CsrfAPIView):
    def post(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "agencies.manage")
        tenant = change_agency_capabilities().execute(
            parse_uuid(agency_id, field="agency_id"),
            _capabilities_from(request.data),
        )
        return success(_agency_payload(tenant))


class AgencyCommissionView(CsrfAPIView):
    def post(self, request: Request, agency_id: str) -> Response:
        context = require_principal(request, PrincipalType.PLATFORM)
        if "commission.edit" not in context.permissions:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        tenant = set_commission_rate().execute(
            parse_uuid(agency_id, field="agency_id"),
            int(request.data.get("commission_rate_bps") or -1),
        )
        return success(_agency_payload(tenant))


class AgencyReassignCustomerView(CsrfAPIView):
    def post(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "agencies.manage")
        parse_uuid(agency_id, field="agency_id")
        raise DomainError(
            "customer_reassign_forbidden",
            "Customer reassignment is not available.",
            http_status=409,
        )
