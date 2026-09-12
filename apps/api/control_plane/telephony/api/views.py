from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.identity.api.auth import (
    parse_uuid,
    require_agency_perm,
    require_customer_perm,
    require_platform_perm,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.telephony.application.assign import AssignNumberCommand
from control_plane.telephony.application.destinations import CreateDestinationCommand
from control_plane.telephony.application.ports import PhoneNumberRecord, ReservationRecord
from control_plane.telephony.application.release import ReleaseNumberCommand
from control_plane.telephony.application.reserve import ReserveNumberCommand
from control_plane.telephony.application.stock import PurchaseNumberCommand, StockNumberCommand
from control_plane.telephony.domain.types import NumberStatus
from control_plane.telephony.infrastructure.container import (
    assign_number,
    manage_destinations,
    numbers,
    purchase_number,
    reconcile_numbers,
    release_number,
    reservation_seconds,
    reserve_number,
    search_numbers,
    stock_number,
    tenant_numbers,
    voice_control,
)
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page
from tenant.calls.domain import TenantCallRecord
from tenant.media.domain import TransferDestinationRecord
from tenant.numbers.domain import NumberAssignmentRecord




def _page(request: Request) -> tuple[int, int]:
    return parse_page(request.query_params.get("limit"), request.query_params.get("offset"))


def _int_field(data: dict, name: str, default: int | None = None) -> int:
    raw = data.get(name, default)
    if raw is None:
        raise DomainError("validation_error", f"{name} is required.")
    if type(raw) is bool or type(raw) is float:
        raise DomainError("validation_error", f"{name} must be an integer.")
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise DomainError("validation_error", f"{name} must be an integer.") from exc


def _number_payload(row: PhoneNumberRecord) -> dict[str, object]:
    return {
        "id": str(row.id),
        "e164": row.e164,
        "country": row.country,
        "area": row.area,
        "capabilities": list(row.capabilities),
        "provider": row.provider,
        "status": row.status.value,
        "monthly_cost_minor": row.monthly_cost.minor_units,
        "currency": row.monthly_cost.currency,
        "assigned_agency_id": (
            str(row.assigned_tenant_id) if row.assigned_tenant_id else None
        ),
        "assigned_customer_id": (
            str(row.assigned_customer_id) if row.assigned_customer_id else None
        ),
        "assigned_agent_id": str(row.assigned_agent_id) if row.assigned_agent_id else None,
        "reserved_until": row.reserved_until.isoformat() if row.reserved_until else None,
    }


def _reservation_payload(row: ReservationRecord) -> dict[str, object]:
    return {
        "id": str(row.id),
        "number_id": str(row.number_id),
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "agent_id": str(row.agent_id),
        "status": row.status.value,
        "expires_at": row.expires_at.isoformat(),
    }


def _assignment_payload(row: NumberAssignmentRecord) -> dict[str, object]:
    return {
        "id": str(row.assignment_id),
        "number_id": str(row.phone_number_id),
        "e164": row.e164,
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "agent_id": str(row.agent_id),
        "status": row.status.value,
        "invoice_id": str(row.invoice_id) if row.invoice_id else None,
        "assigned_at": row.assigned_at.isoformat(),
        "released_at": row.released_at.isoformat() if row.released_at else None,
    }


class PlatformNumberCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "number.view")
        status_raw = str(request.query_params.get("status") or "").strip()
        try:
            status = NumberStatus(status_raw) if status_raw else None
        except ValueError as exc:
            raise DomainError("validation_error", "status is invalid.") from exc
        rows = numbers().list(
            status=status,
            country=str(request.query_params.get("country") or ""),
            area=str(request.query_params.get("area") or ""),
            capability=str(request.query_params.get("capability") or ""),
        )
        limit, offset = parse_page(
            request.query_params.get("limit"), request.query_params.get("offset")
        )
        slice_rows, page = page_slice(rows, offset, limit)
        return success([_number_payload(row) for row in slice_rows], page=page)

    def post(self, request: Request) -> Response:
        require_platform_perm(request, "number.view")
        data = request.data if isinstance(request.data, dict) else {}
        if bool(data.get("purchase")):
            row = purchase_number().execute(
                PurchaseNumberCommand(
                    e164=str(data.get("e164") or ""),
                    actor_id=require_platform_perm(request, "number.view").user.id,
                    idempotency_key=str(request.headers.get("Idempotency-Key") or ""),
                )
            )
        else:
            row = stock_number().execute(
                StockNumberCommand(
                    e164=str(data.get("e164") or ""),
                    country=str(data.get("country") or "US"),
                    area=str(data.get("area") or ""),
                    capabilities=data.get("capabilities"),
                    monthly_cost_minor=_int_field(data, "monthly_cost_minor", 0),
                    provider=str(data.get("provider") or "platform"),
                    provider_ref=str(data.get("provider_ref") or ""),
                )
            )
        return success(_number_payload(row), status=201)


class PlatformNumberReleaseView(CsrfAPIView):
    def post(self, request: Request, number_id: str) -> Response:
        require_platform_perm(request, "number.view")
        data = request.data if isinstance(request.data, dict) else {}
        row = release_number().execute(
            ReleaseNumberCommand(
                number_id=parse_uuid(number_id, field="number_id"),
                tenant_id=None,
                confirm=bool(data.get("confirm")),
                privileged=True,
                provider_release=bool(data.get("provider_release")),
            )
        )
        return success(_number_payload(row))


class PlatformNumberReconcileView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        require_platform_perm(request, "number.view")
        result = reconcile_numbers().execute()
        return success(
            {
                "expired_reservations": result.expired_reservations,
                "provider_orphans": list(result.provider_orphans),
                "local_orphans": list(result.local_orphans),
            }
        )


class AgencyNumberSearchView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "number.view")
        result = search_numbers().execute(
            country=str(request.query_params.get("country") or ""),
            area=str(request.query_params.get("area") or ""),
            capability=str(request.query_params.get("capability") or ""),
            tenant_id=context.membership.tenant_id,
            include_provider=True,
        )
        limit, offset = parse_page(
            request.query_params.get("limit"), request.query_params.get("offset")
        )
        slice_rows, page = page_slice(result.inventory, offset, limit)
        return success(
            {
                "inventory": [_number_payload(row) for row in slice_rows],
                "offers": [
                    {
                        "e164": offer.e164,
                        "country": offer.country,
                        "area": offer.area,
                        "capabilities": list(offer.capabilities),
                        "monthly_cost_minor": offer.monthly_cost.minor_units,
                        "provider": offer.provider,
                    }
                    for offer in result.offers
                ],
            },
            page=page,
        )


class AgencyNumberCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "number.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        assigned = numbers().list(status=NumberStatus.ASSIGNED, tenant_id=tenant_id)
        rows = tenant_numbers().list_assignments(tenant_id)
        limit, offset = parse_page(
            request.query_params.get("limit"), request.query_params.get("offset")
        )
        slice_rows, page = page_slice(rows, offset, limit)
        return success(
            {
                "assigned": [_number_payload(row) for row in assigned],
                "assignments": [_assignment_payload(row) for row in slice_rows],
            },
            page=page,
        )


class AgencyNumberReserveView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "number.create")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        data = request.data if isinstance(request.data, dict) else {}
        reserved = reserve_number().execute(
            ReserveNumberCommand(
                tenant_id=tenant_id,
                agent_id=parse_uuid(data.get("agent_id"), field="agent_id"),
                number_id=parse_uuid(data.get("number_id"), field="number_id"),
                reservation_seconds=reservation_seconds(),
            )
        )
        return success(_reservation_payload(reserved), status=201)


class AgencyNumberAssignView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "number.update")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        data = request.data if isinstance(request.data, dict) else {}
        result = assign_number().execute(
            AssignNumberCommand(
                tenant_id=tenant_id,
                reservation_id=parse_uuid(
                    data.get("reservation_id"), field="reservation_id"
                ),
                actor_id=context.user.id,
                confirm=bool(data.get("confirm")),
                idempotency_key=str(request.headers.get("Idempotency-Key") or ""),
            )
        )
        return success(
            {
                "assignment": _assignment_payload(result.assignment),
                "invoice": {
                    "id": str(result.invoice.invoice_id),
                    "total_minor": result.invoice.total_minor,
                    "currency": result.invoice.currency,
                    "status": result.invoice.status.value,
                    "kind": result.invoice.lines[0].kind.value,
                },
            },
            status=201,
        )


class AgencyNumberReleaseView(CsrfAPIView):
    def post(self, request: Request, number_id: str) -> Response:
        context = require_agency_perm(request, "number.delete")
        data = request.data if isinstance(request.data, dict) else {}
        row = release_number().execute(
            ReleaseNumberCommand(
                number_id=parse_uuid(number_id, field="number_id"),
                tenant_id=context.membership.tenant_id,
                confirm=bool(data.get("confirm")),
            )
        )
        return success(_number_payload(row))


def _destination_payload(row: TransferDestinationRecord, *, disabled: bool = False) -> dict:
    return {
        "id": str(row.destination_id),
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "kind": row.kind.value,
        "label": row.label,
        "target": row.target,
        "members": [
            {"kind": member.kind.value, "target": member.target, "label": member.label}
            for member in row.members
        ],
        "no_answer_seconds": row.no_answer_seconds,
        "status": "disabled" if disabled else row.status.value,
        "platform_disabled": disabled,
    }


def _call_payload(row: TenantCallRecord) -> dict[str, object]:
    return {
        "id": str(row.call_id),
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "agent_id": str(row.agent_id),
        "e164": row.e164,
        "remote_e164": row.remote_e164,
        "edge_call_id": row.edge_call_id,
        "direction": row.direction.value,
        "status": row.status.value,
        "billed_minutes": row.billed_minutes,
        "duration_seconds": row.duration_seconds,
        "end_reason": row.end_reason,
        "voicemail_status": row.voicemail_status,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "ended_at": row.ended_at.isoformat() if row.ended_at else None,
    }


class AgencyTransferCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "transfer.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        customer_id = request.query_params.get("customer_id")
        rows = manage_destinations().list(
            tenant_id=tenant_id,
            customer_id=parse_uuid(customer_id, field="customer_id") if customer_id else None,
        )
        limit, offset = _page(request)
        sliced, page = page_slice(rows, offset, limit)
        return success([_destination_payload(row) for row in sliced], page=page)

    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "transfer.create")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        data = request.data if isinstance(request.data, dict) else {}
        members = data.get("members") or []
        if type(members) is not list:
            raise DomainError("validation_error", "members must be a list.")
        row = manage_destinations().create(
            CreateDestinationCommand(
                tenant_id=tenant_id,
                customer_id=parse_uuid(data.get("customer_id"), field="customer_id"),
                kind=str(data.get("kind") or ""),
                label=str(data.get("label") or ""),
                target=str(data.get("target") or ""),
                members=tuple(item for item in members if type(item) is dict),
                no_answer_seconds=_int_field(data, "no_answer_seconds", 25),
            )
        )
        return success(_destination_payload(row), status=201)


class AgencyTransferDisableView(CsrfAPIView):
    def post(self, request: Request, destination_id: str) -> Response:
        context = require_agency_perm(request, "transfer.update")
        row = manage_destinations().disable(
            destination_id=parse_uuid(destination_id, field="destination_id"),
            tenant_id=context.membership.tenant_id,
            privileged=False,
        )
        return success(_destination_payload(row))


class PlatformTransferCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "transfer.view")
        from control_plane.telephony.infrastructure.repositories import (
            DjangoTransferIndexRepository,
        )

        rows = DjangoTransferIndexRepository().list()
        limit, offset = _page(request)
        sliced, page = page_slice(rows, offset, limit)
        return success(
            [
                {
                    "id": str(row.id),
                    "agency_id": str(row.tenant_id),
                    "customer_id": str(row.customer_id),
                    "kind": row.kind,
                    "label": row.label,
                    "status": row.status,
                    "platform_disabled": row.platform_disabled,
                }
                for row in sliced
            ],
            page=page,
        )


class PlatformTransferDisableView(CsrfAPIView):
    def post(self, request: Request, destination_id: str) -> Response:
        require_platform_perm(request, "transfer.view")
        data = request.data if isinstance(request.data, dict) else {}
        if not bool(data.get("confirm")):
            raise DomainError("validation_error", "confirm is required.")
        row = manage_destinations().disable(
            destination_id=parse_uuid(destination_id, field="destination_id"),
            tenant_id=None,
            privileged=True,
        )
        return success(_destination_payload(row, disabled=True))


class AgencyCallCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "call.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        customer_id = request.query_params.get("customer_id")
        rows = voice_control().list_tenant_calls(
            tenant_id=tenant_id,
            customer_id=parse_uuid(customer_id, field="customer_id") if customer_id else None,
        )
        limit, offset = _page(request)
        sliced, page = page_slice(rows, offset, limit)
        return success([_call_payload(row) for row in sliced], page=page)


class AgencyOutboundCallView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "call.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        data = request.data if isinstance(request.data, dict) else {}
        payload = voice_control().originate(
            tenant_id=tenant_id,
            agent_id=parse_uuid(data.get("agent_id"), field="agent_id"),
            to=str(data.get("to") or ""),
            actor_id=context.user.id,
            idempotency_key=str(request.headers.get("Idempotency-Key") or ""),
        )
        return success(payload, status=201)


class CustomerCallCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_customer_perm(request, "call.view")
        membership = context.membership
        assert membership.tenant_id is not None and membership.customer_id is not None
        rows = voice_control().list_tenant_calls(
            tenant_id=membership.tenant_id,
            customer_id=membership.customer_id,
        )
        limit, offset = _page(request)
        sliced, page = page_slice(rows, offset, limit)
        return success([_call_payload(row) for row in sliced], page=page)


class PlatformCallCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "call.view")
        tenant_id = request.query_params.get("agency_id")
        customer_id = request.query_params.get("customer_id")
        rows = voice_control().list_index_calls(
            tenant_id=parse_uuid(tenant_id, field="agency_id") if tenant_id else None,
            customer_id=parse_uuid(customer_id, field="customer_id") if customer_id else None,
        )
        limit, offset = _page(request)
        sliced, page = page_slice(rows, offset, limit)
        return success(
            [
                {
                    "id": str(row.call_id),
                    "agency_id": str(row.tenant_id),
                    "customer_id": str(row.customer_id),
                    "agent_id": str(row.agent_id),
                    "e164": row.e164,
                    "remote_e164": row.remote_e164,
                    "edge_call_id": row.edge_call_id,
                    "direction": row.direction.value,
                    "status": row.status.value,
                    "voicemail_status": row.voicemail_status,
                    "billed_minutes": row.billed_minutes,
                }
                for row in sliced
            ],
            page=page,
        )
