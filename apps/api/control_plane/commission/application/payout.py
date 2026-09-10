from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from django.db import transaction

from control_plane.commission.application.ports import (
    CommissionIdempotencyRepository,
    LedgerEntryRecord,
    LedgerRepository,
    PayoutProofRecord,
    PayoutProofRepository,
    PayoutRecord,
    PayoutRepository,
)
from control_plane.commission.domain.policies import (
    assert_payout_amount,
    assert_payout_transition,
    payout_not_found,
)
from control_plane.commission.domain.types import LedgerKind, PayoutStatus
from control_plane.commission.domain.wallet import LedgerView, available_money, project_wallet
from control_plane.kyc.application.ports import KycCaseRepository
from control_plane.kyc.domain.policies import assert_payout_eligible
from control_plane.tenancy.application.ports import Clock, TenantRepository
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from shared_kernel.money import Money

logger = logging.getLogger("vokit.commission")


def _views(rows: list[LedgerEntryRecord]) -> tuple[LedgerView, ...]:
    return tuple(
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


@dataclass(frozen=True, slots=True)
class RequestPayoutCommand:
    tenant_id: uuid.UUID
    amount_minor: int
    method_label: str
    actor_id: uuid.UUID
    idempotency_key: str


class RequestAgencyPayout:
    def __init__(
        self,
        ledger: LedgerRepository,
        payouts: PayoutRepository,
        keys: CommissionIdempotencyRepository,
        cases: KycCaseRepository,
        tenants: TenantRepository,
        clock: Clock,
    ) -> None:
        self._ledger = ledger
        self._payouts = payouts
        self._keys = keys
        self._cases = cases
        self._tenants = tenants
        self._clock = clock

    def execute(self, command: RequestPayoutCommand) -> PayoutRecord:
        tenant = self._tenants.get(command.tenant_id)
        if tenant is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        case = self._cases.get_for_tenant(command.tenant_id)
        assert_payout_eligible(
            kyc_status=case.status if case is not None else None,
            frozen=bool(case.frozen) if case is not None else False,
            agency_status=tenant.agency_status,
            capabilities=tenant.capabilities,
        )
        key = command.idempotency_key.strip()
        if not key:
            raise DomainError("validation_error", "Idempotency-Key is required.")
        replay = self._keys.get(command.actor_id, key)
        if replay is not None:
            existing = self._payouts.get(replay)
            if existing is None:
                raise DomainError("not_found", "Resource not found.", http_status=404)
            return existing
        amount = Money(command.amount_minor)
        with transaction.atomic():
            self._ledger.lock_tenant(command.tenant_id)
            rows = self._ledger.list_for_tenant(command.tenant_id)
            buckets = project_wallet(_views(rows), self._clock.now())
            assert_payout_amount(amount, available_money(buckets))
            now = self._clock.now()
            payout_id = new_uuid7()
            payout = PayoutRecord(
                id=payout_id,
                tenant_id=command.tenant_id,
                amount_minor=amount.minor_units,
                currency=amount.currency,
                status=PayoutStatus.REQUESTED,
                method_label=command.method_label.strip()[:64] or "bank",
                transaction_ref="",
                receipt_number="",
                requested_by_id=command.actor_id,
                decided_by_id=None,
                requested_at=now,
                paid_at=None,
            )
            self._payouts.create(payout)
            self._ledger.append(
                _money_entry(
                    tenant_id=command.tenant_id,
                    kind=LedgerKind.PAYOUT_RESERVED,
                    amount=amount,
                    payout_id=payout_id,
                    actor_id=command.actor_id,
                    reason="payout_reserved",
                    now=now,
                )
            )
            self._keys.create(command.actor_id, key, payout_id)
        log_event(
            logger,
            "payout.requested",
            outcome="success",
            tenant_id=str(command.tenant_id),
            payout_id=str(payout_id),
        )
        return payout


@dataclass(frozen=True, slots=True)
class DecidePayoutCommand:
    payout_id: uuid.UUID
    action: str
    actor_id: uuid.UUID
    transaction_ref: str = ""


class DecidePayout:
    def __init__(
        self,
        ledger: LedgerRepository,
        payouts: PayoutRepository,
        proofs: PayoutProofRepository,
        clock: Clock,
    ) -> None:
        self._ledger = ledger
        self._payouts = payouts
        self._proofs = proofs
        self._clock = clock

    def execute(self, command: DecidePayoutCommand) -> PayoutRecord:
        payout = self._payouts.get(command.payout_id)
        if payout is None:
            raise payout_not_found()
        nxt = assert_payout_transition(payout.status, command.action)
        now = self._clock.now()
        receipt = payout.receipt_number
        paid_at = payout.paid_at
        ref = payout.transaction_ref
        if command.action == "reject" and payout.status is not PayoutStatus.REJECTED:
            self._release(payout, command.actor_id, now)
        if command.action == "mark_paid":
            if self._proofs.get(payout.id) is None:
                raise DomainError(
                    "payout_proof_required",
                    "Private payout proof is required before marking paid.",
                    http_status=409,
                )
            receipt = f"VKT-PO-{payout.id.hex[:12].upper()}"
            paid_at = now
            ref = command.transaction_ref.strip()[:64]
            self._ledger.append(
                _money_entry(
                    tenant_id=payout.tenant_id,
                    kind=LedgerKind.PAYOUT_PAID,
                    amount=Money(payout.amount_minor, payout.currency),
                    payout_id=payout.id,
                    actor_id=command.actor_id,
                    reason="payout_paid",
                    now=now,
                )
            )
        updated = PayoutRecord(
            id=payout.id,
            tenant_id=payout.tenant_id,
            amount_minor=payout.amount_minor,
            currency=payout.currency,
            status=nxt,
            method_label=payout.method_label,
            transaction_ref=ref,
            receipt_number=receipt,
            requested_by_id=payout.requested_by_id,
            decided_by_id=command.actor_id,
            requested_at=payout.requested_at,
            paid_at=paid_at,
        )
        self._payouts.update_status(updated)
        log_event(
            logger,
            "payout.decided",
            outcome="success",
            tenant_id=str(payout.tenant_id),
            payout_id=str(payout.id),
            status=nxt.value,
        )
        return updated

    def _release(self, payout: PayoutRecord, actor_id: uuid.UUID, now: datetime) -> None:
        already = any(
            row.kind is LedgerKind.PAYOUT_RELEASED and row.payout_id == payout.id
            for row in self._ledger.list_for_tenant(payout.tenant_id)
        )
        if already:
            return
        self._ledger.append(
            _money_entry(
                tenant_id=payout.tenant_id,
                kind=LedgerKind.PAYOUT_RELEASED,
                amount=Money(payout.amount_minor, payout.currency),
                payout_id=payout.id,
                actor_id=actor_id,
                reason="payout_rejected",
                now=now,
            )
        )


@dataclass(frozen=True, slots=True)
class UploadProofCommand:
    payout_id: uuid.UUID
    object_ref: str
    content_type: str
    checksum: str
    actor_id: uuid.UUID


class UploadPayoutProof:
    def __init__(self, payouts: PayoutRepository, proofs: PayoutProofRepository) -> None:
        self._payouts = payouts
        self._proofs = proofs

    def execute(self, command: UploadProofCommand) -> PayoutProofRecord:
        payout = self._payouts.get(command.payout_id)
        if payout is None:
            raise payout_not_found()
        if payout.status is PayoutStatus.PAID:
            raise DomainError(
                "payout_already_paid",
                "Paid payouts cannot accept new proof.",
                http_status=409,
            )
        object_ref = command.object_ref.strip()
        checksum = command.checksum.strip()
        content_type = command.content_type.strip() or "application/octet-stream"
        if not object_ref or not checksum:
            raise DomainError("validation_error", "object_ref and checksum are required.")
        if object_ref.startswith("http://") or object_ref.startswith("https://"):
            raise DomainError("validation_error", "Proof must be an object reference.")
        existing = self._proofs.get(payout.id)
        if existing is not None:
            return existing
        record = PayoutProofRecord(
            payout_id=payout.id,
            object_ref=object_ref[:255],
            content_type=content_type[:128],
            checksum=checksum[:128],
            uploaded_by_id=command.actor_id,
        )
        self._proofs.create(record)
        log_event(
            logger,
            "payout.proof.uploaded",
            outcome="success",
            tenant_id=str(payout.tenant_id),
            payout_id=str(payout.id),
        )
        return record


def _money_entry(
    *,
    tenant_id: uuid.UUID,
    kind: LedgerKind,
    amount: Money,
    payout_id: uuid.UUID,
    actor_id: uuid.UUID,
    reason: str,
    now: datetime,
) -> LedgerEntryRecord:
    return LedgerEntryRecord(
        id=new_uuid7(),
        tenant_id=tenant_id,
        customer_id=None,
        kind=kind,
        amount_minor=amount.minor_units,
        currency=amount.currency,
        payment_id=None,
        invoice_id=None,
        commission_id=None,
        payout_id=payout_id,
        eligible_base_minor=None,
        rate_bps_snapshot=None,
        earned_at=now,
        available_at=now,
        reason=reason,
        actor_id=actor_id,
        created_at=now,
    )
