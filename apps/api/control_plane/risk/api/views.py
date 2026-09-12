from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.customers.domain.policies import customer_not_found
from control_plane.customers.infrastructure.container import customer_index
from control_plane.identity.api.auth import (
    parse_uuid,
    require_agency_perm,
    require_customer_perm,
    require_platform_perm,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.risk.application.create_agent import CreateAgentCommand
from control_plane.risk.application.override import OverrideRiskCommand
from control_plane.risk.application.ports import RiskCaseRecord
from control_plane.risk.application.submit_verification import SubmitVerificationCommand
from control_plane.risk.domain.policies import assert_agency_cannot_override
from control_plane.risk.domain.types import RiskStatus, VerificationStatus
from control_plane.risk.infrastructure.container import (
    create_agent,
    override_risk,
    risk_cases,
    submit_verification,
    tenant_agents,
    verifications,
)
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page


def _case_payload(row: RiskCaseRecord) -> dict[str, object]:
    return {
        "id": str(row.id),
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "status": row.status.value,
        "permanently_banned": row.permanently_banned,
        "note": row.note,
        "last_event_id": row.last_event_id,
    }


def _empty_case(customer_id, tenant_id) -> dict[str, object]:
    return {
        "id": None,
        "agency_id": str(tenant_id),
        "customer_id": str(customer_id),
        "status": RiskStatus.NORMAL.value,
        "permanently_banned": False,
        "note": "",
        "last_event_id": "",
    }


def _agent_payload(row) -> dict[str, object]:
    return {
        "id": str(row.agent_id),
        "agency_id": str(row.tenant_id),
        "customer_id": str(row.customer_id),
        "display_name": row.display_name,
        "status": row.status.value,
    }


def _bool_field(data: dict, name: str) -> bool:
    raw = data.get(name, False)
    if type(raw) is not bool:
        raise DomainError("validation_error", f"{name} must be a boolean.")
    return raw


def _int_field(data: dict, name: str) -> int:
    raw = data.get(name)
    if type(raw) is bool or type(raw) is float:
        raise DomainError("validation_error", f"{name} must be an integer.")
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise DomainError("validation_error", f"{name} must be an integer.") from exc


class PlatformRiskCaseCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "risk.review")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        status_raw = str(request.query_params.get("status") or "").strip()
        try:
            status = RiskStatus(status_raw) if status_raw else None
        except ValueError as exc:
            raise DomainError("validation_error", "status is invalid.") from exc
        rows, page = page_slice(risk_cases().list(status=status), offset, limit)
        return success([_case_payload(row) for row in rows], page=page)


class PlatformRiskOverrideView(CsrfAPIView):
    def post(self, request: Request, case_id: str) -> Response:
        require_platform_perm(request, "risk.review")
        try:
            status = RiskStatus(str(request.data.get("status") or "").strip())
        except ValueError as exc:
            raise DomainError("validation_error", "status is invalid.") from exc
        case = override_risk().execute(
            OverrideRiskCommand(
                case_id=parse_uuid(case_id, field="case_id"),
                status=status,
                note=str(request.data.get("note") or ""),
                privileged=True,
            )
        )
        return success(_case_payload(case))


class AgencyCustomerRiskView(CsrfAPIView):
    def get(self, request: Request, customer_id: str) -> Response:
        context = require_agency_perm(request, "customer.update")
        customer = customer_index().get(parse_uuid(customer_id, field="customer_id"))
        if customer is None or customer.tenant_id != context.membership.tenant_id:
            raise customer_not_found()
        case = risk_cases().get_for_customer(customer.id)
        payload = (
            _case_payload(case)
            if case is not None
            else _empty_case(customer.id, customer.tenant_id)
        )
        return success(payload)


class AgencyCustomerRiskOverrideView(CsrfAPIView):
    def post(self, request: Request, customer_id: str) -> Response:
        require_agency_perm(request, "customer.update")
        parse_uuid(customer_id, field="customer_id")
        assert_agency_cannot_override()
        return success({})


class AgencyCustomerAgentCollectionView(CsrfAPIView):
    def get(self, request: Request, customer_id: str) -> Response:
        context = require_agency_perm(request, "agent.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        customer = customer_index().get(parse_uuid(customer_id, field="customer_id"))
        if customer is None or customer.tenant_id != tenant_id:
            raise customer_not_found()
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows, page = page_slice(
            tenant_agents().list_agents(tenant_id, customer.id), offset, limit
        )
        return success([_agent_payload(row) for row in rows], page=page)

    def post(self, request: Request, customer_id: str) -> Response:
        context = require_agency_perm(request, "agent.create")
        agent = create_agent().execute(
            CreateAgentCommand(
                customer_id=parse_uuid(customer_id, field="customer_id"),
                display_name=str(request.data.get("display_name") or ""),
                actor_tenant_id=context.membership.tenant_id,
                privileged=False,
            )
        )
        return success(_agent_payload(agent), status=201)


class CustomerRiskView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_customer_perm(request, "risk.verify")
        membership = context.membership
        assert membership.tenant_id is not None and membership.customer_id is not None
        case = risk_cases().get_for_customer(membership.customer_id)
        return success(
            _case_payload(case)
            if case is not None
            else _empty_case(membership.customer_id, membership.tenant_id)
        )


class CustomerVerificationView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_customer_perm(request, "risk.verify")
        membership = context.membership
        assert membership.customer_id is not None
        case = risk_cases().get_for_customer(membership.customer_id)
        if case is None:
            return success({"status": VerificationStatus.INCOMPLETE.value})
        latest = verifications().latest_for_case(case.id)
        if latest is None:
            return success({"status": VerificationStatus.INCOMPLETE.value})
        return success(
            {
                "id": str(latest.id),
                "status": latest.status.value,
                "card_last4": latest.card_last4,
                "id_object_ref": latest.id_object_ref,
                "card_object_ref": latest.card_object_ref,
            }
        )

    def post(self, request: Request) -> Response:
        context = require_customer_perm(request, "risk.verify")
        membership = context.membership
        assert membership.customer_id is not None
        record = submit_verification().execute(
            SubmitVerificationCommand(
                customer_id=membership.customer_id,
                actor_customer_id=membership.customer_id,
                privileged=False,
                payload=dict(request.data),
                id_object_ref=str(request.data.get("id_object_ref") or ""),
                id_content_type=str(request.data.get("id_content_type") or ""),
                id_checksum=str(request.data.get("id_checksum") or ""),
                card_object_ref=str(request.data.get("card_object_ref") or ""),
                card_checksum=str(request.data.get("card_checksum") or ""),
                card_last4=str(request.data.get("card_last4") or ""),
                visible_digit_count=_int_field(request.data, "visible_digit_count"),
                cvv_visible=_bool_field(request.data, "cvv_visible"),
                full_pan_present=_bool_field(request.data, "full_pan_present"),
            )
        )
        return success(
            {
                "id": str(record.id),
                "status": record.status.value,
                "card_last4": record.card_last4,
            },
            status=201,
        )


class CustomerAgentCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_customer_perm(request, "agent.view")
        membership = context.membership
        assert membership.tenant_id is not None and membership.customer_id is not None
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows, page = page_slice(
            tenant_agents().list_agents(membership.tenant_id, membership.customer_id),
            offset,
            limit,
        )
        return success([_agent_payload(row) for row in rows], page=page)
