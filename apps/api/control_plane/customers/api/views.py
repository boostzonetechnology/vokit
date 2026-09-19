from __future__ import annotations

from datetime import UTC, datetime

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.billing.application.adjust_minutes import AdjustCustomerMinutesCommand
from control_plane.billing.domain.policies import assigned_plan_is_payment_due
from control_plane.billing.infrastructure.container import (
    adjust_customer_minutes,
    get_customer_subscription,
    get_customer_usage,
    tenant_billing,
)
from control_plane.customers.application.create_customer import CreateCustomerCommand
from control_plane.customers.domain.policies import BanKey, customer_not_found
from control_plane.customers.domain.types import CustomerStatus
from control_plane.customers.infrastructure.container import (
    ban_index,
    change_customer_status,
    create_customer,
    customer_index,
    update_customer_profile,
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
        "plan_id": str(row.plan_id) if row.plan_id else None,
        "remaining_minutes": row.remaining_minutes,
        "payment_due": row.payment_due,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _subscription_dict(view) -> dict[str, object]:
    sub = view.subscription
    return {
        "id": str(sub.subscription_id),
        "plan_id": str(sub.plan_id),
        "plan_version_id": str(sub.plan_version_id),
        "plan_name": view.plan_name,
        "plan_version": view.plan_version,
        "status": sub.status.value,
        "included_minutes": view.included_minutes,
        "period_end": view.period_end.isoformat() if view.period_end else None,
        "pending_kind": sub.pending_kind,
        "pending_effective_at": sub.pending_effective_at.isoformat()
        if sub.pending_effective_at
        else None,
    }


def _directory_payload(row) -> dict[str, object]:
    """Platform directory row: index fields + usage/subscription summary for the page slice."""
    payload = _index_payload(row)
    usage = get_customer_usage().execute(row.id)
    payload["remaining_minutes"] = usage.remaining_minutes
    subscription = get_customer_subscription().execute(row.id)
    if subscription is not None:
        payload["plan_name"] = subscription.plan_name
        payload["plan_version"] = subscription.plan_version
        payload["subscription_status"] = subscription.subscription.status.value
    else:
        payload["plan_name"] = None
        payload["plan_version"] = None
        payload["subscription_status"] = None
    return payload


def _enrich_customer_detail(
    payload: dict[str, object], customer_id, tenant_id
) -> dict[str, object]:
    usage = get_customer_usage().execute(customer_id)
    payload["remaining_minutes"] = usage.remaining_minutes
    view = get_customer_subscription().execute(customer_id)
    payload["subscription"] = _subscription_dict(view) if view else None
    payload["payment_due"] = _live_payment_due(
        tenant_id,
        customer_id,
        view.subscription if view else None,
    )
    return payload


def _parse_time(raw: object, field: str) -> datetime | None:
    if raw in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError as exc:
        raise DomainError("validation_error", f"{field} is invalid.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _parse_optional_bool(raw: object, field: str) -> bool | None:
    if raw in (None, ""):
        return None
    value = str(raw).strip().lower()
    if value in {"true", "1"}:
        return True
    if value in {"false", "0"}:
        return False
    raise DomainError("validation_error", f"{field} is invalid.")


def _parse_optional_int(raw: object, field: str) -> int | None:
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise DomainError("validation_error", f"{field} is invalid.") from exc


def _live_payment_due(tenant_id, customer_id, subscription) -> bool:
    if subscription is None:
        return False
    return assigned_plan_is_payment_due(
        subscription.subscription_id,
        tenant_billing().list_invoices(tenant_id, customer_id),
    )


def _profile_fields(data: dict) -> dict[str, str | None]:
    fields: dict[str, str | None] = {}
    for name in ("display_name", "legal_name", "phone", "country", "timezone"):
        if name in data:
            fields[name] = None if data.get(name) is None else str(data.get(name) or "")
    return fields


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
            plan_id=parse_optional_uuid(
                request.query_params.get("plan_id"), field="plan_id"
            ),
            payment_due=_parse_optional_bool(
                request.query_params.get("payment_due"), field="payment_due"
            ),
            remaining_minutes_max=_parse_optional_int(
                request.query_params.get("remaining_minutes_max"),
                field="remaining_minutes_max",
            ),
            updated_after=_parse_time(
                request.query_params.get("updated_after"), "updated_after"
            ),
            updated_before=_parse_time(
                request.query_params.get("updated_before"), "updated_before"
            ),
        )
        sliced, page = page_slice(rows, offset, limit)
        return success([_directory_payload(row) for row in sliced], page=page)

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
        return success(
            _enrich_customer_detail(
                _customer_payload(row), identifier, indexed.tenant_id
            )
        )

    def patch(self, request: Request, customer_id: str) -> Response:
        context = require_platform_perm(request, "customer.update")
        identifier = parse_uuid(customer_id, field="customer_id")
        indexed = customer_index().get(identifier)
        if indexed is None:
            raise customer_not_found()
        data = request.data if isinstance(request.data, dict) else {}
        row = update_customer_profile().execute(
            customer_id=identifier,
            tenant_id=indexed.tenant_id,
            privileged=True,
            actor_id=context.user.id,
            actor_role=context.membership.role,
            **_profile_fields(data),
        )
        return success(_customer_payload(row))


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


class AgencyCustomerUsageView(CsrfAPIView):
    def get(self, request: Request, customer_id: str) -> Response:
        context = require_agency_perm(request, "customer.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        identifier = parse_uuid(customer_id, field="customer_id")
        indexed = customer_index().get(identifier)
        if indexed is None or indexed.tenant_id != tenant_id:
            raise customer_not_found()
        snapshot = get_customer_usage().execute(identifier)
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
        identifier = parse_uuid(customer_id, field="customer_id")
        row = lifecycle().get_customer(tenant_id, identifier)
        if row is None:
            raise customer_not_found()
        return success(
            _enrich_customer_detail(_customer_payload(row), identifier, tenant_id)
        )

    def patch(self, request: Request, customer_id: str) -> Response:
        context = require_agency_perm(request, "customer.update")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        data = request.data if isinstance(request.data, dict) else {}
        row = update_customer_profile().execute(
            customer_id=parse_uuid(customer_id, field="customer_id"),
            tenant_id=tenant_id,
            privileged=False,
            actor_id=context.user.id,
            actor_role=context.membership.role,
            **_profile_fields(data),
        )
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
