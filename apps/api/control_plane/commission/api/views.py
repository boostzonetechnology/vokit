from __future__ import annotations

from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.commission.application.adjust import AdjustWalletCommand
from control_plane.commission.application.freeze import FreezeWalletCommand
from control_plane.commission.application.payout import (
    DecidePayoutCommand,
    RequestPayoutCommand,
    SetProofAgencyVisibilityCommand,
    UploadProofCommand,
)
from control_plane.commission.application.payout_methods import UpsertPayoutMethodCommand
from control_plane.commission.application.reverse import ReverseCommissionCommand
from control_plane.commission.domain.payout_method import mask_account_identifier
from control_plane.commission.domain.policies import payout_not_found
from control_plane.commission.domain.types import PayoutStatus
from control_plane.commission.domain.wallet import (
    LedgerView,
    commission_state,
    project_wallet,
)
from control_plane.commission.infrastructure.container import (
    adjust_wallet,
    decide_payout,
    freeze_wallet,
    ledger,
    manage_payout_methods,
    payouts,
    proofs,
    request_payout,
    reverse_commission,
    set_proof_agency_visibility,
    upload_proof,
)
from control_plane.identity.api.auth import (
    parse_optional_uuid,
    parse_uuid,
    require_agency_perm,
    require_platform_perm,
)
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.kyc.domain.policies import payout_block_reason
from control_plane.kyc.domain.types import KycStatus
from control_plane.kyc.infrastructure.container import kyc_cases
from control_plane.platform_settings.infrastructure.container import platform_settings
from control_plane.tenancy.infrastructure.container import tenant_repo
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page


def _wallet_payload(tenant_id, now) -> dict[str, object]:
    rows = ledger().list_for_tenant(tenant_id)
    views = tuple(
        LedgerView(
            id=row.id,
            kind=row.kind,
            amount_minor=row.amount_minor,
            currency=row.currency,
            commission_id=row.commission_id,
            payout_id=row.payout_id,
            earned_at=row.earned_at,
            available_at=row.available_at,
        )
        for row in rows
    )
    buckets = project_wallet(views, now)
    return buckets.as_money()


def _entry_payload(row, rows, now) -> dict[str, object]:
    view = LedgerView(
        id=row.id,
        kind=row.kind,
        amount_minor=row.amount_minor,
        currency=row.currency,
        commission_id=row.commission_id,
        payout_id=row.payout_id,
        earned_at=row.earned_at,
        available_at=row.available_at,
    )
    views = tuple(
        LedgerView(
            id=item.id,
            kind=item.kind,
            amount_minor=item.amount_minor,
            currency=item.currency,
            commission_id=item.commission_id,
            payout_id=item.payout_id,
            earned_at=item.earned_at,
            available_at=item.available_at,
        )
        for item in rows
    )
    payload = {
        "id": str(row.id),
        "kind": row.kind.value,
        "amount_minor": row.amount_minor,
        "currency": row.currency,
        "invoice_id": str(row.invoice_id) if row.invoice_id else None,
        "payment_id": str(row.payment_id) if row.payment_id else None,
        "reason": row.reason,
        "earned_at": row.earned_at.isoformat() if row.earned_at else None,
        "available_at": row.available_at.isoformat() if row.available_at else None,
    }
    if row.kind.value == "commission_earned":
        payload["state"] = commission_state(view, views, now).value
        payload["eligible_base_minor"] = row.eligible_base_minor
        payload["rate_bps_snapshot"] = row.rate_bps_snapshot
    return payload


def _mask_public(value: str) -> str:
    text = (value or "").strip()
    if "*" in text or len(text) <= 4:
        return text
    return f"{'*' * (len(text) - 4)}{text[-4:]}"


def _compliance_payload(tenant_id, now, cache: dict | None = None) -> dict[str, object]:
    if cache is not None and tenant_id in cache:
        return cache[tenant_id]
    tenant = tenant_repo().get(tenant_id)
    case = kyc_cases().get_for_tenant(tenant_id)
    status = case.status if case is not None else None
    frozen = bool(case.frozen) if case is not None else False
    agency_status = tenant.agency_status if tenant is not None else None
    capabilities = tenant.capabilities if tenant is not None else None
    block = None
    if tenant is not None:
        block = payout_block_reason(
            kyc_status=status,
            frozen=frozen,
            agency_status=agency_status,
            capabilities=capabilities,
        )
    buckets = project_wallet(
        tuple(
            LedgerView(
                id=row.id,
                kind=row.kind,
                amount_minor=row.amount_minor,
                currency=row.currency,
                commission_id=row.commission_id,
                payout_id=row.payout_id,
                earned_at=row.earned_at,
                available_at=row.available_at,
            )
            for row in ledger().list_for_tenant(tenant_id)
        ),
        now,
    )
    payload = {
        "agency_status": agency_status.value if agency_status is not None else None,
        "kyc_status": status.value if status is not None else KycStatus.NOT_STARTED.value,
        "kyc_frozen": frozen,
        "payout_eligible": block is None and tenant is not None,
        "wallet_frozen": buckets.frozen_minor > 0,
    }
    if cache is not None:
        cache[tenant_id] = payload
    return payload


def _payout_public(row, *, now=None, cache: dict | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": str(row.id),
        "agency_id": str(row.tenant_id),
        "amount_minor": row.amount_minor,
        "currency": row.currency,
        "status": row.status.value,
        "method_label": row.method_label,
        "transaction_ref": row.transaction_ref,
        "receipt_number": row.receipt_number or None,
        "requested_at": row.requested_at.isoformat() if row.requested_at else None,
        "paid_at": row.paid_at.isoformat() if row.paid_at else None,
    }
    if now is not None:
        payload["compliance"] = _compliance_payload(row.tenant_id, now, cache)
    return payload


def _receipt_payload(row) -> dict[str, object]:
    if row.status is not PayoutStatus.PAID or not row.receipt_number:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    tenant = tenant_repo().get(row.tenant_id)
    return {
        "receipt_number": row.receipt_number,
        "payout_id": str(row.id),
        "agency_id": str(row.tenant_id),
        "agency_display_name": tenant.display_name if tenant is not None else "",
        "agency_legal_name": tenant.legal_name if tenant is not None else "",
        "amount_minor": row.amount_minor,
        "currency": row.currency,
        "method_label": _mask_public(row.method_label),
        "transaction_ref": _mask_public(row.transaction_ref),
        "status": row.status.value,
        "requested_at": row.requested_at.isoformat() if row.requested_at else None,
        "paid_at": row.paid_at.isoformat() if row.paid_at else None,
        "issuer": platform_settings().receipt_issuer(),
        "disclaimer": (
            "This receipt confirms payout processing and is not the underlying banking proof."
        ),
    }


def _method_public(row) -> dict[str, object]:
    return {
        "id": str(row.id),
        "beneficiary_name": row.beneficiary_name,
        "account_identifier_masked": mask_account_identifier(row.account_identifier),
        "bank_name": row.bank_name,
        "country": row.country,
        "currency": row.currency,
        "label": row.label,
        "status": row.status.value,
        "is_default": row.is_default,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _proof_public(row, *, for_agency: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "payout_id": str(row.payout_id),
        "object_ref": row.object_ref,
        "content_type": row.content_type,
        "checksum": row.checksum,
        "agency_visible": bool(row.agency_visible),
        "agency_visible_at": (
            row.agency_visible_at.isoformat() if row.agency_visible_at else None
        ),
        "has_file": True,
    }
    if not for_agency:
        payload["uploaded_by_id"] = str(row.uploaded_by_id)
        payload["agency_visible_by"] = (
            str(row.agency_visible_by) if row.agency_visible_by else None
        )
    return payload


def _proof_file_response(proof) -> Response:
    from django.http import FileResponse

    from control_plane.commission.infrastructure.proof_storage import resolve_proof_path

    path = resolve_proof_path(proof.object_ref)
    content_type = proof.content_type or "application/octet-stream"
    response = FileResponse(path.open("rb"), content_type=content_type)
    response["Content-Disposition"] = f'inline; filename="{path.name}"'
    return response


class AgencyWalletView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "wallet.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        now = SystemClock().now()
        rows = ledger().list_for_tenant(tenant_id)
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        sliced, page = page_slice(rows, offset, limit)
        return success(
            {
                "buckets": _wallet_payload(tenant_id, now),
                "entries": [_entry_payload(row, rows, now) for row in sliced],
            },
            page=page,
        )


class AgencyPayoutCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "wallet.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows, page = page_slice(payouts().list(tenant_id=tenant_id), offset, limit)
        return success([_payout_public(row) for row in rows], page=page)

    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "payout.request")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        raw = request.data.get("amount_minor", 0)
        if type(raw) is bool or type(raw) is float:
            raise DomainError("validation_error", "amount_minor must be an integer.")
        try:
            amount_minor = int(raw)
        except (TypeError, ValueError) as exc:
            raise DomainError("validation_error", "amount_minor must be an integer.") from exc
        payout = request_payout().execute(
            RequestPayoutCommand(
                tenant_id=tenant_id,
                amount_minor=amount_minor,
                actor_id=context.user.id,
                idempotency_key=str(request.headers.get("Idempotency-Key") or ""),
                payout_method_id=parse_optional_uuid(
                    request.data.get("payout_method_id"), field="payout_method_id"
                ),
                method_label=str(request.data.get("method_label") or ""),
            )
        )
        return success(_payout_public(payout), status=201)


class AgencyPayoutMethodCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = require_agency_perm(request, "wallet.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        rows = manage_payout_methods().list(tenant_id)
        usable_only = str(request.query_params.get("usable") or "").lower() in {
            "1",
            "true",
            "yes",
        }
        if usable_only:
            from control_plane.commission.domain.types import PayoutMethodStatus

            rows = [row for row in rows if row.status is PayoutMethodStatus.USABLE]
        return success([_method_public(row) for row in rows])

    def post(self, request: Request) -> Response:
        context = require_agency_perm(request, "payout.request")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        created = manage_payout_methods().upsert(
            UpsertPayoutMethodCommand(
                tenant_id=tenant_id,
                beneficiary_name=str(request.data.get("beneficiary_name") or ""),
                account_identifier=str(request.data.get("account_identifier") or ""),
                bank_name=str(request.data.get("bank_name") or ""),
                country=str(request.data.get("country") or ""),
                currency=str(request.data.get("currency") or "USD"),
                is_default=bool(request.data.get("is_default")),
            )
        )
        return success(_method_public(created), status=201)


class AgencyPayoutMethodDetailView(CsrfAPIView):
    def patch(self, request: Request, method_id: str) -> Response:
        context = require_agency_perm(request, "payout.request")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        existing = manage_payout_methods().get_for_tenant(
            tenant_id, parse_uuid(method_id, field="method_id")
        )
        updated = manage_payout_methods().upsert(
            UpsertPayoutMethodCommand(
                tenant_id=tenant_id,
                method_id=existing.id,
                beneficiary_name=str(
                    request.data.get("beneficiary_name") or existing.beneficiary_name
                ),
                account_identifier=str(
                    request.data.get("account_identifier") or existing.account_identifier
                ),
                bank_name=str(request.data.get("bank_name") or existing.bank_name),
                country=str(request.data.get("country") or existing.country),
                currency=str(request.data.get("currency") or existing.currency),
                is_default=(
                    bool(request.data.get("is_default"))
                    if "is_default" in request.data
                    else existing.is_default
                ),
            )
        )
        return success(_method_public(updated))

    def post(self, request: Request, method_id: str) -> Response:
        context = require_agency_perm(request, "payout.request")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        action = str(request.data.get("action") or "enable").strip().lower()
        if action != "enable":
            raise DomainError(
                "validation_error",
                "Unsupported action. Use action=enable.",
                http_status=400,
            )
        enabled = manage_payout_methods().enable(
            tenant_id, parse_uuid(method_id, field="method_id")
        )
        return success(_method_public(enabled))

    def delete(self, request: Request, method_id: str) -> Response:
        context = require_agency_perm(request, "payout.request")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        disabled = manage_payout_methods().disable(
            tenant_id, parse_uuid(method_id, field="method_id")
        )
        return success(_method_public(disabled))


class AgencyPayoutReceiptView(CsrfAPIView):
    def get(self, request: Request, payout_id: str) -> Response:
        context = require_agency_perm(request, "wallet.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        payout = payouts().get(parse_uuid(payout_id, field="payout_id"))
        if payout is None or payout.tenant_id != tenant_id:
            raise payout_not_found()
        return success(_receipt_payload(payout))


class AgencyPayoutProofView(CsrfAPIView):
    def get(self, request: Request, payout_id: str) -> Response:
        context = require_agency_perm(request, "wallet.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        payout = payouts().get(parse_uuid(payout_id, field="payout_id"))
        if payout is None or payout.tenant_id != tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        proof = proofs().get(payout.id)
        if proof is None or not proof.agency_visible:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return success(_proof_public(proof, for_agency=True))


class AgencyPayoutProofFileView(CsrfAPIView):
    def get(self, request: Request, payout_id: str) -> Response:
        context = require_agency_perm(request, "wallet.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        payout = payouts().get(parse_uuid(payout_id, field="payout_id"))
        if payout is None or payout.tenant_id != tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        proof = proofs().get(payout.id)
        if proof is None or not proof.agency_visible:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return _proof_file_response(proof)


class PlatformWalletView(CsrfAPIView):
    def get(self, request: Request, agency_id: str) -> Response:
        require_platform_perm(request, "billing.view")
        tenant_id = parse_uuid(agency_id, field="agency_id")
        now = SystemClock().now()
        return success({"agency_id": str(tenant_id), "buckets": _wallet_payload(tenant_id, now)})


class PlatformPayoutCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        require_platform_perm(request, "billing.view")
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        status_raw = str(request.query_params.get("status") or "").strip()
        try:
            status = PayoutStatus(status_raw) if status_raw else None
        except ValueError as exc:
            raise DomainError("validation_error", "status is invalid.") from exc
        agency_id = parse_optional_uuid(
            request.query_params.get("agency_id"), field="agency_id"
        )
        rows, page = page_slice(
            payouts().list(tenant_id=agency_id, status=status), offset, limit
        )
        now = SystemClock().now()
        cache: dict = {}
        return success(
            [_payout_public(row, now=now, cache=cache) for row in rows], page=page
        )


class PlatformPayoutDetailView(CsrfAPIView):
    def get(self, request: Request, payout_id: str) -> Response:
        require_platform_perm(request, "billing.view")
        payout = payouts().get(parse_uuid(payout_id, field="payout_id"))
        if payout is None:
            raise payout_not_found()
        return success(_payout_public(payout, now=SystemClock().now(), cache={}))


class PlatformPayoutActionView(CsrfAPIView):
    def post(self, request: Request, payout_id: str) -> Response:
        context = require_platform_perm(request, "payout.approve")
        payout = decide_payout().execute(
            DecidePayoutCommand(
                payout_id=parse_uuid(payout_id, field="payout_id"),
                action=str(request.data.get("action") or ""),
                actor_id=context.user.id,
                transaction_ref=str(request.data.get("transaction_ref") or ""),
            )
        )
        return success(_payout_public(payout))


class PlatformPayoutProofView(CsrfAPIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get(self, request: Request, payout_id: str) -> Response:
        require_platform_perm(request, "payout.approve")
        proof = proofs().get(parse_uuid(payout_id, field="payout_id"))
        if proof is None:
            raise payout_not_found()
        return success(_proof_public(proof))

    def post(self, request: Request, payout_id: str) -> Response:
        from control_plane.commission.infrastructure.proof_storage import store_proof_file

        context = require_platform_perm(request, "payout.approve")
        payout_uuid = parse_uuid(payout_id, field="payout_id")
        upload = None
        if getattr(request, "FILES", None) is not None:
            upload = request.FILES.get("file")
        if upload is None and hasattr(request, "data"):
            candidate = request.data.get("file")
            if hasattr(candidate, "read"):
                upload = candidate
        if upload is not None:
            object_ref, content_type, checksum = store_proof_file(
                payout_id=payout_uuid,
                filename=str(getattr(upload, "name", "") or "proof"),
                content_type=str(getattr(upload, "content_type", "") or ""),
                content=upload.read(),
            )
        else:
            object_ref = str(request.data.get("object_ref") or "")
            content_type = str(request.data.get("content_type") or "")
            checksum = str(request.data.get("checksum") or "")
        proof = upload_proof().execute(
            UploadProofCommand(
                payout_id=payout_uuid,
                object_ref=object_ref,
                content_type=content_type,
                checksum=checksum,
                actor_id=context.user.id,
            )
        )
        raw_visible = request.data.get("agency_visible")
        if raw_visible is not None:
            if isinstance(raw_visible, bool):
                visible = raw_visible
            else:
                visible = str(raw_visible).strip().lower() in {"1", "true", "yes", "on"}
            proof = set_proof_agency_visibility().execute(
                SetProofAgencyVisibilityCommand(
                    payout_id=payout_uuid,
                    agency_visible=visible,
                    actor_id=context.user.id,
                )
            )
        return success(_proof_public(proof), status=201)

    def patch(self, request: Request, payout_id: str) -> Response:
        context = require_platform_perm(request, "payout.approve")
        if "agency_visible" not in request.data:
            raise DomainError(
                "validation_error",
                "agency_visible is required.",
                http_status=400,
            )
        raw = request.data.get("agency_visible")
        if isinstance(raw, bool):
            visible = raw
        else:
            visible = str(raw).strip().lower() in {"1", "true", "yes", "on"}
        proof = set_proof_agency_visibility().execute(
            SetProofAgencyVisibilityCommand(
                payout_id=parse_uuid(payout_id, field="payout_id"),
                agency_visible=visible,
                actor_id=context.user.id,
            )
        )
        return success(_proof_public(proof))


class PlatformPayoutProofFileView(CsrfAPIView):
    def get(self, request: Request, payout_id: str) -> Response:
        require_platform_perm(request, "payout.approve")
        proof = proofs().get(parse_uuid(payout_id, field="payout_id"))
        if proof is None:
            raise payout_not_found()
        return _proof_file_response(proof)


class PlatformPayoutMarkPaidView(CsrfAPIView):
    def post(self, request: Request, payout_id: str) -> Response:
        context = require_platform_perm(request, "payout.approve")
        payout = decide_payout().execute(
            DecidePayoutCommand(
                payout_id=parse_uuid(payout_id, field="payout_id"),
                action="mark_paid",
                actor_id=context.user.id,
                transaction_ref=str(request.data.get("transaction_ref") or ""),
            )
        )
        return success(_payout_public(payout))


class PlatformReverseCommissionView(CsrfAPIView):
    def post(self, request: Request) -> Response:
        context = require_platform_perm(request, "commission.edit")
        entry = reverse_commission().execute(
            ReverseCommissionCommand(
                payment_id=parse_uuid(request.data.get("payment_id"), field="payment_id"),
                reason=str(request.data.get("reason") or ""),
                actor_id=context.user.id,
            )
        )
        return success({"id": str(entry.id), "kind": entry.kind.value}, status=201)


class PlatformWalletAdjustView(CsrfAPIView):
    def post(self, request: Request, agency_id: str) -> Response:
        context = require_platform_perm(request, "wallet.adjust")
        raw = request.data.get("amount_minor")
        if type(raw) is bool or type(raw) is float or raw is None:
            raise DomainError("validation_error", "amount_minor must be an integer.")
        try:
            amount_minor = int(raw)
        except (TypeError, ValueError) as exc:
            raise DomainError("validation_error", "amount_minor must be an integer.") from exc
        entry = adjust_wallet().execute(
            AdjustWalletCommand(
                tenant_id=parse_uuid(agency_id, field="agency_id"),
                amount_minor=amount_minor,
                direction=str(request.data.get("direction") or ""),
                reason=str(request.data.get("reason") or ""),
                actor_id=context.user.id,
            )
        )
        return success({"id": str(entry.id), "kind": entry.kind.value}, status=201)


class PlatformWalletFreezeView(CsrfAPIView):
    def post(self, request: Request, agency_id: str) -> Response:
        context = require_platform_perm(request, "wallet.adjust")
        frozen = request.data.get("frozen")
        if type(frozen) is not bool:
            raise DomainError("validation_error", "frozen must be a boolean.")
        entry = freeze_wallet().execute(
            FreezeWalletCommand(
                tenant_id=parse_uuid(agency_id, field="agency_id"),
                frozen=frozen,
                reason=str(request.data.get("reason") or ""),
                actor_id=context.user.id,
            )
        )
        return success({"id": str(entry.id), "kind": entry.kind.value})
