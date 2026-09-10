from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.customers.application.create_customer import CreateCustomerCommand
from control_plane.customers.domain.policies import BanKey, customer_not_found
from control_plane.customers.domain.types import CustomerStatus
from control_plane.customers.infrastructure.container import (
    ban_index,
    change_customer_status,
    create_customer,
    customer_index,
)
from control_plane.identity.api.auth import (
    parse_optional_uuid,
    parse_uuid,
    require_principal,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.infrastructure.container import lifecycle
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page
from tenant.lifecycle.domain import TenantCustomer


def _require_platform_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.PLATFORM)
    if permission not in context.permissions:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _ban_keys(data: dict) -> tuple[BanKey, ...]:
    rows = []
    for item in data.get("ban_keys") or []:
        rows.append(
            BanKey(kind=str(item.get("kind") or ""), value=str(item.get("value") or ""))
        )
    email = str(data.get("owner_email") or "").strip()
    if email:
        rows.append(BanKey(kind="email", value=email))
    return tuple(rows)


def _customer_payload(row: TenantCustomer) -> dict[str, object]:
    return {
        "id": str(row.customer_id),
        "agency_id": str(row.tenant_id),
        "display_name": row.display_name,
        "status": row.status.value,
    }


def _index_payload(row) -> dict[str, object]:
    return {
        "id": str(row.id),
        "agency_id": str(row.tenant_id),
        "display_name": row.display_name,
        "status": row.status.value,
    }


class PlatformCustomerCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "customers.view")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        status_raw = str(request.query_params.get("status") or "").strip()
        try:
            status = CustomerStatus(status_raw) if status_raw else None
        except ValueError as exc:
            raise DomainError("validation_error", "status is invalid.") from exc
        agency_id = parse_optional_uuid(
            request.query_params.get("agency_id"), field="agency_id"
        )
        rows = customer_index().list(
            tenant_id=agency_id,
            status=status,
            query=str(request.query_params.get("q") or ""),
        )
        sliced, page = page_slice(rows, offset, limit)
        return success([_index_payload(row) for row in sliced], page=page)

    def post(self, request: Request) -> Response:
        context = _require_platform_perm(request, "customers.create")
        created = create_customer().execute(
            CreateCustomerCommand(
                display_name=str(request.data.get("display_name") or ""),
                agency_tenant_id=parse_uuid(
                    request.data.get("agency_id"), field="agency_id"
                ),
                actor=context.membership,
                privileged=True,
                owner_email=str(request.data.get("owner_email") or ""),
                customer_id=parse_optional_uuid(
                    request.data.get("customer_id"), field="customer_id"
                ),
                ban_keys=_ban_keys(request.data),
            )
        )
        payload = _customer_payload(created.customer)
        if created.invitation_token:
            payload["owner_invitation_token"] = created.invitation_token
        return success(payload, status=201)


class PlatformCustomerDetailView(CsrfAPIView):
    def get(self, request: Request, customer_id: str) -> Response:
        _require_platform_perm(request, "customers.view")
        identifier = parse_uuid(customer_id, field="customer_id")
        indexed = customer_index().get(identifier)
        if indexed is None:
            raise customer_not_found()
        row = lifecycle().get_customer(indexed.tenant_id, identifier)
        if row is None:
            return success(_index_payload(indexed))
        return success(_customer_payload(row))


class PlatformCustomerStatusView(CsrfAPIView):
    def post(self, request: Request, customer_id: str) -> Response:
        _require_platform_perm(request, "customers.create")
        identifier = parse_uuid(customer_id, field="customer_id")
        indexed = customer_index().get(identifier)
        if indexed is None:
            raise customer_not_found()
        row = change_customer_status().execute(
            customer_id=identifier,
            tenant_id=indexed.tenant_id,
            action=str(request.data.get("action") or ""),
            privileged=True,
        )
        return success(_customer_payload(row))


class AgencyCustomerCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.AGENCY)
        if "customers.manage" not in context.permissions:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        tenant_id = context.membership.tenant_id
        if tenant_id is None:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        parse_optional_uuid(request.query_params.get("tenant_id"), field="tenant_id")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows = lifecycle().list_customers(tenant_id)
        sliced, page = page_slice(rows, offset, limit)
        return success([_customer_payload(row) for row in sliced], page=page)

    def post(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.AGENCY)
        if "customers.manage" not in context.permissions:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        tenant_id = context.membership.tenant_id
        if tenant_id is None:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        created = create_customer().execute(
            CreateCustomerCommand(
                display_name=str(request.data.get("display_name") or ""),
                agency_tenant_id=tenant_id,
                actor=context.membership,
                privileged=False,
                owner_email=str(request.data.get("owner_email") or ""),
                customer_id=None,
                ban_keys=_ban_keys(request.data),
            )
        )
        payload = _customer_payload(created.customer)
        if created.invitation_token:
            payload["owner_invitation_token"] = created.invitation_token
        return success(payload, status=201)


class AgencyCustomerDetailView(CsrfAPIView):
    def get(self, request: Request, customer_id: str) -> Response:
        context = require_principal(request, PrincipalType.AGENCY)
        if "customers.manage" not in context.permissions:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        tenant_id = context.membership.tenant_id
        if tenant_id is None:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        parse_optional_uuid(request.query_params.get("tenant_id"), field="tenant_id")
        row = lifecycle().get_customer(
            tenant_id, parse_uuid(customer_id, field="customer_id")
        )
        if row is None:
            raise customer_not_found()
        return success(_customer_payload(row))


class AgencyCustomerStatusView(CsrfAPIView):
    def post(self, request: Request, customer_id: str) -> Response:
        context = require_principal(request, PrincipalType.AGENCY)
        if "customers.manage" not in context.permissions:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        tenant_id = context.membership.tenant_id
        if tenant_id is None:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        row = change_customer_status().execute(
            customer_id=parse_uuid(customer_id, field="customer_id"),
            tenant_id=tenant_id,
            action=str(request.data.get("action") or ""),
            privileged=False,
        )
        return success(_customer_payload(row))


class CustomerAccountView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.CUSTOMER)
        tenant_id = context.membership.tenant_id
        customer_id = context.membership.customer_id
        if tenant_id is None or customer_id is None:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        claimed = parse_optional_uuid(
            request.query_params.get("customer_id"), field="customer_id"
        )
        if claimed is not None and claimed != customer_id:
            raise customer_not_found()
        row = lifecycle().get_customer(tenant_id, customer_id)
        if row is None:
            raise customer_not_found()
        return success(_customer_payload(row))


class PlatformBanKeyView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        _require_platform_perm(request, "customers.create")
        ban_index().add(
            BanKey(
                kind=str(request.data.get("kind") or ""),
                value=str(request.data.get("value") or ""),
            )
        )
        return success({"accepted": True}, status=201)
