from __future__ import annotations

import json

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from control_plane.identity.api.auth import parse_uuid, require_principal
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.kyc.application.override_case import OverrideKycCommand
from control_plane.kyc.application.ports import (
    KycCaseRecord,
    KycSettingsRecord,
    MappedProviderEvent,
)
from control_plane.kyc.domain.policies import map_provider_status, payout_block_reason
from control_plane.kyc.domain.types import KycStatus
from control_plane.kyc.infrastructure.container import (
    apply_kyc_webhook,
    kyc_cases,
    kyc_settings,
    override_kyc_case,
    request_payout,
    start_kyc_session,
)
from control_plane.kyc.infrastructure.hmac import verify_kyc_signature
from control_plane.tenancy.infrastructure.container import tenant_repo
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page


def _require_platform_perm(request: Request, permission: str):
    context = require_principal(request, PrincipalType.PLATFORM)
    if permission not in context.permissions:
        raise DomainError("forbidden", "Not permitted.", http_status=403)
    return context


def _case_payload(case: KycCaseRecord, *, privileged: bool) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": str(case.id),
        "agency_id": str(case.tenant_id),
        "status": case.status.value,
        "reason_code": case.reason_code,
        "external_note": case.external_note,
        "frozen": case.frozen,
        "session_id": case.session_id,
    }
    if privileged:
        payload["internal_note"] = case.internal_note
        payload["inquiry_id"] = case.inquiry_id
        payload["last_event_id"] = case.last_event_id
    return payload


class AgencyKycView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.AGENCY)
        tenant_id = context.membership.tenant_id
        if tenant_id is None:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        tenant = tenant_repo().get(tenant_id)
        if tenant is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        case = kyc_cases().get_for_tenant(tenant_id)
        status = case.status if case else None
        frozen = bool(case.frozen) if case else False
        block = payout_block_reason(
            kyc_status=status,
            frozen=frozen,
            agency_status=tenant.agency_status,
            capabilities=tenant.capabilities,
        )
        data: dict[str, object] = {
            "status": status.value if status else KycStatus.NOT_STARTED.value,
            "payout_eligible": block is None,
            "payout_block_reason": block,
            "next_step": "start_or_resume_provider_session",
        }
        if case is not None:
            data["case"] = _case_payload(case, privileged=False)
        return success(data)


class AgencyKycSessionView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.AGENCY)
        tenant_id = context.membership.tenant_id
        if tenant_id is None:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        started = start_kyc_session().execute(tenant_id)
        return success(
            {
                "hosted_url": started.session.hosted_url,
                "session_id": started.session.session_id,
                "status": started.case.status.value,
            },
            status=201,
        )


class AgencyPayoutView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_principal(request, PrincipalType.AGENCY)
        if "payout.request" not in context.permissions:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        tenant_id = context.membership.tenant_id
        if tenant_id is None:
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        result = request_payout().execute(tenant_id)
        return success(
            {
                "accepted": result.accepted,
                "kyc_status": result.kyc_status,
                "settlement": "pending_phase7",
            },
            status=202,
        )


class PlatformKycCaseCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "kyc.review")
        status_raw = str(request.query_params.get("status") or "").strip()
        try:
            status = KycStatus(status_raw) if status_raw else None
        except ValueError as exc:
            raise DomainError("validation_error", "status is invalid.") from exc
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows = kyc_cases().list(status=status)
        sliced, page = page_slice(rows, offset, limit)
        return success(
            [_case_payload(row, privileged=True) for row in sliced],
            page=page,
        )


class PlatformKycOverrideView(CsrfAPIView):
    def post(self, request: Request, case_id: str) -> Response:
        _require_platform_perm(request, "kyc.review")
        raw_status = request.data.get("status")
        status = None
        if raw_status not in (None, ""):
            try:
                status = KycStatus(str(raw_status))
            except ValueError as exc:
                raise DomainError("validation_error", "status is invalid.") from exc
        case = override_kyc_case().execute(
            OverrideKycCommand(
                case_id=parse_uuid(case_id, field="case_id"),
                action=str(request.data.get("action") or ""),
                status=status,
                internal_note=str(request.data.get("internal_note") or ""),
            )
        )
        return success(_case_payload(case, privileged=True))


class PlatformKycSettingsView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "kyc.review")
        row = kyc_settings().get()
        return success(
            {
                "provider_slug": row.provider_slug,
                "api_key_ref": row.api_key_ref,
                "webhook_secret_ref": row.webhook_secret_ref,
                "hosted_base_url": row.hosted_base_url,
            }
        )

    def post(self, request: Request) -> Response:
        _require_platform_perm(request, "kyc.review")
        current = kyc_settings().get()
        record = KycSettingsRecord(
            provider_slug=str(request.data.get("provider_slug") or current.provider_slug),
            api_key_ref=str(request.data.get("api_key_ref") or current.api_key_ref),
            webhook_secret_ref=str(
                request.data.get("webhook_secret_ref") or current.webhook_secret_ref
            ),
            hosted_base_url=str(
                request.data.get("hosted_base_url") or current.hosted_base_url
            ),
        )
        kyc_settings().save(record)
        saved = kyc_settings().get()
        return success(
            {
                "provider_slug": saved.provider_slug,
                "api_key_ref": saved.api_key_ref,
                "webhook_secret_ref": saved.webhook_secret_ref,
                "hosted_base_url": saved.hosted_base_url,
            }
        )


class KycWebhookView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request: Request, provider: str) -> Response:
        settings = kyc_settings().get()
        if provider != settings.provider_slug:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        raw = request.body
        verify_kyc_signature(
            secret_ref=settings.webhook_secret_ref,
            raw_body=raw,
            header=request.headers.get("X-Vokit-Kyc-Signature", ""),
        )
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise DomainError("validation_error", "Webhook body is invalid.") from exc
        if not isinstance(data, dict):
            raise DomainError("validation_error", "Webhook body is invalid.")
        event = MappedProviderEvent(
            event_id=str(data.get("event_id") or ""),
            session_id=str(data.get("session_id") or ""),
            inquiry_id=str(data.get("inquiry_id") or ""),
            status=map_provider_status(str(data.get("status") or "")),
            reason_code=str(data.get("reason_code") or ""),
            external_note=str(data.get("external_note") or ""),
        )
        result = apply_kyc_webhook().execute(event)
        return success({"duplicate": result.duplicate, "status": result.status})
