from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.billing.application.adjust_minutes import AdjustCustomerMinutesCommand
from control_plane.billing.infrastructure.container import (
    adjust_customer_minutes,
    get_customer_subscription,
    get_customer_usage,
)
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
    require_agency_perm,
    require_platform_perm,
    require_principal,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.tenancy.infrastructure.container import lifecycle
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page
from tenant.lifecycle.domain import TenantCustomer


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
        "legal_name": row.legal_name,
        "owner_email": row.owner_email,
        "phone": row.phone,
        "country": row.country,
        "timezone": row.timezone,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _index_payload(row) -> dict[str, object]:
    return {
        "id": str(row.id),
        "agency_id": str(row.tenant_id),
        "display_name": row.display_name,
        "status": row.status.value,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


class PlatformCustomerCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "customer.view")
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
        context = require_platform_perm(request, "customer.create")
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
                legal_name=str(request.data.get("legal_name") or ""),
                phone=str(request.data.get("phone") or ""),
                country=str(request.data.get("country") or ""),
                timezone=str(request.data.get("timezone") or ""),
            )
        )
        return success(_customer_payload(created.customer), status=201)


class PlatformCustomerDetailView(CsrfAPIView):
    def get(self, request: Request, customer_id: str) -> Response:
        require_platform_perm(request, "customer.view")
        identifier = parse_uuid(customer_id, field="customer_id")
        indexed = customer_index().get(identifier)
        if indexed is None:
            raise customer_not_found()
        row = lifecycle().get_customer(indexed.tenant_id, identifier)
        if row is None:
            return success(_index_payload(indexed))
        payload = _customer_payload(row)
        usage = get_customer_usage().execute(identifier)
        payload["remaining_minutes"] = usage.remaining_minutes
        subscription = get_customer_subscription().execute(identifier)
        if subscription is not None:
            payload["subscription"] = {
                "id": str(subscription.subscription.subscription_id),
                "plan_id": str(subscription.subscription.plan_id),
                "plan_version_id": str(subscription.subscription.plan_version_id),
                "plan_name": subscription.plan_name,
                "plan_version": subscription.plan_version,
                "status": subscription.subscription.status.value,
                "included_minutes": subscription.included_minutes,
            }
        else:
            payload["subscription"] = None
        return success(payload)


class PlatformCustomerStatusView(CsrfAPIView):
    def post(self, request: Request, customer_id: str) -> Response:
        context = require_platform_perm(request, "customer.update")
        identifier = parse_uuid(customer_id, field="customer_id")
        indexed = customer_index().get(identifier)
        if indexed is None:
            raise customer_not_found()
        row = change_customer_status().execute(
            customer_id=identifier,
            tenant_id=indexed.tenant_id,
            action=str(request.data.get("action") or ""),
            privileged=True,
            reason=str(request.data.get("reason") or ""),
            actor_id=context.user.id,
            actor_role=context.membership.role,
        )
        return success(_customer_payload(row))


class PlatformCustomerUsageView(CsrfAPIView):
    def get(self, request: Request, customer_id: str) -> Response:
        require_platform_perm(request, "customer.view")
        snapshot = get_customer_usage().execute(
            parse_uuid(customer_id, field="customer_id")
        )
        return success(
            {
                "remaining_minutes": snapshot.remaining_minutes,
                "lots": [
                    {
                        "id": str(lot.lot_id),
                        "kind": lot.kind.value,
                        "granted_minutes": lot.granted_minutes,
                        "remaining_minutes": lot.remaining_minutes,
                    }
                    for lot in snapshot.lots
                ],
            }
        )


class PlatformCustomerMinutesAdjustmentView(CsrfAPIView):
    def post(self, request: Request, customer_id: str) -> Response:
        context = require_platform_perm(request, "customer.update")
        raw_minutes = request.data.get("minutes")
        try:
            minutes = int(raw_minutes)
        except (TypeError, ValueError) as exc:
            raise DomainError("validation_error", "minutes must be a non-zero integer.") from exc
        snapshot = adjust_customer_minutes().execute(
            AdjustCustomerMinutesCommand(
                customer_id=parse_uuid(customer_id, field="customer_id"),
                minutes=minutes,
                reason=str(request.data.get("reason") or ""),
                actor_id=context.user.id,
                actor_role=context.membership.role,
            )
        )
        return success(
            {
                "remaining_minutes": snapshot.remaining_minutes,
                "lots": [
                    {
                        "id": str(lot.lot_id),
                        "kind": lot.kind.value,
                        "granted_minutes": lot.granted_minutes,
                        "remaining_minutes": lot.remaining_minutes,
                    }
                    for lot in snapshot.lots
                ],
            },
            status=201,
        )


class AgencyCustomerCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "customer.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        parse_optional_uuid(request.query_params.get("tenant_id"), field="tenant_id")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows = lifecycle().list_customers(tenant_id)
        sliced, page = page_slice(rows, offset, limit)
        return success([_customer_payload(row) for row in sliced], page=page)

    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "customer.create")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        created = create_customer().execute(
            CreateCustomerCommand(
                display_name=str(request.data.get("display_name") or ""),
                agency_tenant_id=tenant_id,
                actor=context.membership,
                privileged=False,
                owner_email=str(request.data.get("owner_email") or ""),
                customer_id=None,
                ban_keys=_ban_keys(request.data),
                legal_name=str(request.data.get("legal_name") or ""),
                phone=str(request.data.get("phone") or ""),
                country=str(request.data.get("country") or ""),
                timezone=str(request.data.get("timezone") or ""),
            )
        )
        return success(_customer_payload(created.customer), status=201)


class AgencyCustomerDetailView(CsrfAPIView):
    def get(self, request: Request, customer_id: str) -> Response:
        context = require_agency_perm(request, "customer.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        parse_optional_uuid(request.query_params.get("tenant_id"), field="tenant_id")
        row = lifecycle().get_customer(
            tenant_id, parse_uuid(customer_id, field="customer_id")
        )
        if row is None:
            raise customer_not_found()
        return success(_customer_payload(row))


class AgencyCustomerStatusView(CsrfAPIView):
    def post(self, request: Request, customer_id: str) -> Response:
        context = require_agency_perm(request, "customer.update")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        row = change_customer_status().execute(
            customer_id=parse_uuid(customer_id, field="customer_id"),
            tenant_id=tenant_id,
            action=str(request.data.get("action") or ""),
            privileged=False,
            reason=str(request.data.get("reason") or ""),
            actor_id=context.user.id,
            actor_role=context.membership.role,
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
        require_platform_perm(request, "customer.create")
        ban_index().add(
            BanKey(
                kind=str(request.data.get("kind") or ""),
                value=str(request.data.get("value") or ""),
            )
        )
        return success({"accepted": True}, status=201)
