from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response

from control_plane.commission.application.adjust import AdjustWalletCommand
from control_plane.commission.application.freeze import FreezeWalletCommand
from control_plane.commission.application.payout import (
    DecidePayoutCommand,
    RequestPayoutCommand,
    UploadProofCommand,
)
from control_plane.commission.application.reverse import ReverseCommissionCommand
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
    payouts,
    proofs,
    request_payout,
    reverse_commission,
    upload_proof,
)
from control_plane.identity.api.auth import parse_optional_uuid, parse_uuid, require_principal
from control_plane.identity.api.views import CsrfAPIView
from control_plane.identity.domain.types import PrincipalType
from control_plane.identity.infrastructure.clock import SystemClock
from shared_kernel.errors import DomainError
from shared_kernel.http.envelope import success
from shared_kernel.http.pagination import page_slice, parse_page


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


def _payout_public(row) -> dict[str, object]:
    return {
        "id": str(row.id),
        "agency_id": str(row.tenant_id),
        "amount_minor": row.amount_minor,
        "currency": row.currency,
        "status": row.status.value,
        "method_label": row.method_label,
        "transaction_ref": row.transaction_ref,
        "receipt_number": row.receipt_number or None,
        "paid_at": row.paid_at.isoformat() if row.paid_at else None,
    }


def _receipt_payload(row) -> dict[str, object]:
    if row.status is not PayoutStatus.PAID or not row.receipt_number:
        raise DomainError("not_found", "Resource not found.", http_status=404)
    return {
        "receipt_number": row.receipt_number,
        "payout_id": str(row.id),
        "agency_id": str(row.tenant_id),
        "amount_minor": row.amount_minor,
        "currency": row.currency,
        "method_label": row.method_label,
        "transaction_ref": row.transaction_ref,
        "status": row.status.value,
        "requested_at": row.requested_at.isoformat() if row.requested_at else None,
        "paid_at": row.paid_at.isoformat() if row.paid_at else None,
    }


class AgencyWalletView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        context = _require_agency_perm(request, "wallet.view")
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
        context = _require_agency_perm(request, "wallet.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        limit, offset = parse_page(
            request.query_params.get("limit"),
            request.query_params.get("offset"),
        )
        rows, page = page_slice(payouts().list(tenant_id=tenant_id), offset, limit)
        return success([_payout_public(row) for row in rows], page=page)

    def post(self, request: Request) -> Response:
        context = _require_agency_perm(request, "payout.request")
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
                method_label=str(request.data.get("method_label") or "bank"),
                actor_id=context.user.id,
                idempotency_key=str(request.headers.get("Idempotency-Key") or ""),
            )
        )
        return success(_payout_public(payout), status=201)


class AgencyPayoutReceiptView(CsrfAPIView):
    def get(self, request: Request, payout_id: str) -> Response:
        context = _require_agency_perm(request, "wallet.view")
        tenant_id = context.membership.tenant_id
        assert tenant_id is not None
        payout = payouts().get(parse_uuid(payout_id, field="payout_id"))
        if payout is None or payout.tenant_id != tenant_id:
            raise payout_not_found()
        return success(_receipt_payload(payout))


class AgencyPayoutProofView(CsrfAPIView):
    def get(self, request: Request, payout_id: str) -> Response:
        _require_agency_perm(request, "wallet.view")
        raise DomainError("not_found", "Resource not found.", http_status=404)


class PlatformWalletView(CsrfAPIView):
    def get(self, request: Request, agency_id: str) -> Response:
        _require_platform_perm(request, "billing.view")
        tenant_id = parse_uuid(agency_id, field="agency_id")
        now = SystemClock().now()
        return success({"agency_id": str(tenant_id), "buckets": _wallet_payload(tenant_id, now)})


class PlatformPayoutCollectionView(CsrfAPIView):
    def get(self, request: Request) -> Response:
        _require_platform_perm(request, "billing.view")
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
        return success([_payout_public(row) for row in rows], page=page)


class PlatformPayoutActionView(CsrfAPIView):
    def post(self, request: Request, payout_id: str) -> Response:
        context = _require_platform_perm(request, "payout.approve")
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
    def get(self, request: Request, payout_id: str) -> Response:
        _require_platform_perm(request, "payout.approve")
        proof = proofs().get(parse_uuid(payout_id, field="payout_id"))
        if proof is None:
            raise payout_not_found()
        return success(
            {
                "payout_id": str(proof.payout_id),
                "object_ref": proof.object_ref,
                "content_type": proof.content_type,
                "checksum": proof.checksum,
            }
        )

    def post(self, request: Request, payout_id: str) -> Response:
        context = _require_platform_perm(request, "payout.approve")
        proof = upload_proof().execute(
            UploadProofCommand(
                payout_id=parse_uuid(payout_id, field="payout_id"),
                object_ref=str(request.data.get("object_ref") or ""),
                content_type=str(request.data.get("content_type") or ""),
                checksum=str(request.data.get("checksum") or ""),
                actor_id=context.user.id,
            )
        )
        return success(
            {
                "payout_id": str(proof.payout_id),
                "object_ref": proof.object_ref,
                "content_type": proof.content_type,
                "checksum": proof.checksum,
            },
            status=201,
        )


class PlatformPayoutMarkPaidView(CsrfAPIView):
    def post(self, request: Request, payout_id: str) -> Response:
        context = _require_platform_perm(request, "payout.approve")
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
        context = _require_platform_perm(request, "commission.edit")
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
        context = _require_platform_perm(request, "wallet.adjust")
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
        context = _require_platform_perm(request, "wallet.adjust")
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
