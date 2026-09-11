from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.billing.domain.types import InvoiceStatus
from control_plane.billing.infrastructure.container import invoice_index
from control_plane.commission.api.views import _payout_public, _wallet_payload
from control_plane.commission.domain.types import LedgerKind
from control_plane.commission.infrastructure.container import ledger, payouts
from control_plane.identity.api.auth import parse_uuid, require_principal
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.tenancy.application.create_agency import CreateAgencyCommand
from control_plane.tenancy.application.notes import CreateAgencyNoteCommand
from control_plane.tenancy.application.ports import TenantRecord
from control_plane.tenancy.domain.lifecycle import AgencyCapabilities, AgencyStatus
from control_plane.tenancy.infrastructure.container import (
    change_agency_capabilities,
    change_agency_status,
    create_agency,
    create_agency_note,
    database_repo,
    list_agency_notes,
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


def _capabilities_from(
    data: dict, current: AgencyCapabilities | None = None
) -> AgencyCapabilities:
    caps = data.get("capabilities") or {}
    if not isinstance(caps, dict):
        caps = {}
    base = current if current is not None else AgencyCapabilities()

    def _flag(key: str, fallback: bool) -> bool:
        if key not in caps:
            return fallback
        return bool(caps.get(key))

    return AgencyCapabilities(
        create_customers=_flag("create_customers", base.create_customers),
        create_agents=_flag("create_agents", base.create_agents),
        purchase_numbers=_flag("purchase_numbers", base.purchase_numbers),
        request_payouts=_flag("request_payouts", base.request_payouts),
        existing_customer_services=_flag(
            "existing_customer_services", base.existing_customer_services
        ),
    )


def _agency_payload(tenant: TenantRecord) -> dict[str, object]:
    caps = tenant.capabilities
    payload: dict[str, object] = {
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
    database = database_repo().get_for_tenant(tenant.id)
    if database is not None:
        payload["database"] = {
            "host": database.host,
            "port": database.port,
            "name": database.name,
            "username": database.db_username,
            "status": database.status.value,
            "schema_version": database.schema_version,
            "tls_required": database.tls_required,
        }
    return payload


class AgencyCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "agencies.view")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows = tenant_repo().list()
        status_raw = str(request.query_params.get("status") or "").strip()
        if status_raw:
            try:
                status = AgencyStatus(status_raw)
            except ValueError as exc:
                raise DomainError("validation_error", "status is invalid.") from exc
            rows = [row for row in rows if row.agency_status is status]
        name = str(request.query_params.get("name") or "").strip().lower()
        if name:
            rows = [
                row
                for row in rows
                if name in row.display_name.lower() or name in row.legal_name.lower()
            ]
        sliced, page = page_slice(rows, offset, limit)
        return success([_agency_payload(row) for row in sliced], page=page)

    def post(self, request: Request) -> Response:
        context = _require_platform_perm(request, "agencies.create")
        db = request.data.get("database") or {}
        if not isinstance(db, dict):
            raise DomainError("validation_error", "database must be an object.")
        if "name" in db:
            raise DomainError(
                "validation_error",
                "database.name must not be supplied; the server allocates names.",
                http_status=400,
            )
        db_port_raw = db.get("port")
        db_port = int(db_port_raw) if db_port_raw not in (None, "") else None
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
                db_username=str(db.get("username") or ""),
                db_password=str(db.get("password") or ""),
                db_host=str(db.get("host") or "") or None,
                db_port=db_port,
            )
        )
        return success(_agency_payload(created.tenant), status=201)


class AgencyDetailView(CsrfAPIView):
    def get(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "agencies.view")
        tenant = tenant_repo().get(parse_uuid(agency_id, field="agency_id"))
        if tenant is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return success(_agency_payload(tenant))

    def patch(self, request: Request, agency_id: str) -> Response:
        context = _require_platform_perm(request, "agencies.manage")
        tenant = update_agency_profile().execute(
            parse_uuid(agency_id, field="agency_id"),
            display_name=request.data.get("display_name"),
            legal_name=request.data.get("legal_name"),
            actor_id=context.user.id,
            actor_role=context.membership.role,
        )
        return success(_agency_payload(tenant))


class AgencyStatusView(CsrfAPIView):
    def post(self, request: Request, agency_id: str) -> Response:
        context = _require_platform_perm(request, "agencies.manage")
        tenant = change_agency_status().execute(
            parse_uuid(agency_id, field="agency_id"),
            str(request.data.get("action") or ""),
            reason=str(request.data.get("reason") or ""),
            actor_id=context.user.id,
            actor_role=context.membership.role,
        )
        return success(_agency_payload(tenant))


class AgencyCapabilitiesView(CsrfAPIView):
    def post(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "agencies.manage")
        tenant_id = parse_uuid(agency_id, field="agency_id")
        current = tenant_repo().get(tenant_id)
        if current is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        tenant = change_agency_capabilities().execute(
            tenant_id,
            _capabilities_from(request.data, current=current.capabilities),
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
            actor_id=context.user.id,
            actor_role=context.membership.role,
        )
        return success(_agency_payload(tenant))


class AgencyFinanceView(CsrfAPIView):
    def get(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "billing.view")
        tenant_id = parse_uuid(agency_id, field="agency_id")
        if tenant_repo().get(tenant_id) is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        now = SystemClock().now()
        invoices = invoice_index().list(tenant_id=tenant_id)
        revenue_minor = sum(
            row.total.minor_units
            for row in invoices
            if row.status is InvoiceStatus.PAID
        )
        earned_minor = sum(
            row.amount_minor
            for row in ledger().list_for_tenant(tenant_id)
            if row.kind is LedgerKind.COMMISSION_EARNED
        )
        payout_rows = payouts().list(tenant_id=tenant_id)
        return success(
            {
                "agency_id": str(tenant_id),
                "buckets": _wallet_payload(tenant_id, now),
                "customer_revenue_minor": revenue_minor,
                "commission_earned_minor": earned_minor,
                "payouts": [_payout_public(row) for row in payout_rows],
            }
        )


class AgencyNotesView(CsrfAPIView):
    def get(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "agencies.view")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows = list_agency_notes().execute(parse_uuid(agency_id, field="agency_id"))
        sliced, page = page_slice(rows, offset, limit)
        return success(
            [
                {
                    "id": str(row.id),
                    "agency_id": str(row.tenant_id),
                    "body": row.body,
                    "risk_flag": row.risk_flag,
                    "created_by_id": str(row.created_by_id),
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in sliced
            ],
            page=page,
        )

    def post(self, request: Request, agency_id: str) -> Response:
        context = _require_platform_perm(request, "agencies.manage")
        note = create_agency_note().execute(
            CreateAgencyNoteCommand(
                tenant_id=parse_uuid(agency_id, field="agency_id"),
                body=str(request.data.get("body") or ""),
                risk_flag=bool(request.data.get("risk_flag") or False),
                actor_id=context.user.id,
                actor_role=context.membership.role,
            )
        )
        return success(
            {
                "id": str(note.id),
                "agency_id": str(note.tenant_id),
                "body": note.body,
                "risk_flag": note.risk_flag,
                "created_by_id": str(note.created_by_id),
                "created_at": note.created_at.isoformat() if note.created_at else None,
            },
            status=201,
        )


class AgencyReassignCustomerView(CsrfAPIView):
    def post(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "agencies.manage")
        parse_uuid(agency_id, field="agency_id")
        raise DomainError(
            "customer_reassign_forbidden",
            "Customer reassignment is not available.",
            http_status=409,
        )
