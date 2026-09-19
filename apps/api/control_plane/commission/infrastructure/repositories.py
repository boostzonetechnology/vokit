from __future__ import annotations

import uuid

from django.db import IntegrityError, transaction

from control_plane.commission.application.ports import (
    LedgerEntryRecord,
    PayoutMethodRecord,
    PayoutProofRecord,
    PayoutRecord,
)
from control_plane.commission.domain.types import LedgerKind, PayoutMethodStatus, PayoutStatus
from control_plane.commission.models import (
    AgencyPayoutMethod,
    CommissionIdempotencyKey,
    LedgerEntry,
    Payout,
    PayoutProof,
    WalletLock,
)
from shared_kernel.errors import DomainError


def _entry(row: LedgerEntry) -> LedgerEntryRecord:
    return LedgerEntryRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        customer_id=row.customer_id,
        kind=LedgerKind(row.kind),
        amount_minor=int(row.amount_minor),
        currency=row.currency,
        payment_id=row.payment_id,
        invoice_id=row.invoice_id,
        commission_id=row.commission_id,
        payout_id=row.payout_id,
        eligible_base_minor=row.eligible_base_minor,
        rate_bps_snapshot=row.rate_bps_snapshot,
        earned_at=row.earned_at,
        available_at=row.available_at,
        reason=row.reason,
        actor_id=row.actor_id,
        created_at=row.created_at,
    )


def _payout(row: Payout) -> PayoutRecord:
    return PayoutRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        amount_minor=int(row.amount_minor),
        currency=row.currency,
        status=PayoutStatus(row.status),
        method_label=row.method_label,
        transaction_ref=row.transaction_ref,
        receipt_number=row.receipt_number,
        requested_by_id=row.requested_by_id,
        decided_by_id=row.decided_by_id,
        requested_at=row.requested_at,
        paid_at=row.paid_at,
    )


class DjangoLedgerRepository:
    def append(self, entry: LedgerEntryRecord) -> None:
        try:
            LedgerEntry.objects.create(
                id=entry.id,
                tenant_id=entry.tenant_id,
                customer_id=entry.customer_id,
                kind=entry.kind.value,
                amount_minor=entry.amount_minor,
                currency=entry.currency,
                payment_id=entry.payment_id,
                invoice_id=entry.invoice_id,
                commission_id=entry.commission_id,
                payout_id=entry.payout_id,
                eligible_base_minor=entry.eligible_base_minor,
                rate_bps_snapshot=entry.rate_bps_snapshot,
                earned_at=entry.earned_at,
                available_at=entry.available_at,
                reason=entry.reason,
                actor_id=entry.actor_id,
            )
        except IntegrityError as exc:
            raise DomainError(
                "ledger_duplicate",
                "Ledger entry already exists for this reference.",
                http_status=409,
            ) from exc

    def list_for_tenant(self, tenant_id: uuid.UUID) -> list[LedgerEntryRecord]:
        rows = LedgerEntry.objects.filter(tenant_id=tenant_id).order_by("created_at", "id")
        return [_entry(row) for row in rows]

    def list_all(self) -> list[LedgerEntryRecord]:
        rows = LedgerEntry.objects.order_by("created_at", "id")
        return [_entry(row) for row in rows]

    def get(self, entry_id: uuid.UUID) -> LedgerEntryRecord | None:
        row = LedgerEntry.objects.filter(id=entry_id).first()
        return _entry(row) if row else None

    def get_earned_by_payment(self, payment_id: uuid.UUID) -> LedgerEntryRecord | None:
        row = LedgerEntry.objects.filter(
            kind=LedgerKind.COMMISSION_EARNED.value, payment_id=payment_id
        ).first()
        return _entry(row) if row else None

    def has_hold_release(self, commission_id: uuid.UUID) -> bool:
        return LedgerEntry.objects.filter(
            kind=LedgerKind.HOLD_RELEASED.value, commission_id=commission_id
        ).exists()

    def lock_tenant(self, tenant_id: uuid.UUID) -> None:
        WalletLock.objects.select_for_update().get_or_create(tenant_id=tenant_id)


class DjangoPayoutRepository:
    def create(self, record: PayoutRecord) -> None:
        Payout.objects.create(
            id=record.id,
            tenant_id=record.tenant_id,
            amount_minor=record.amount_minor,
            currency=record.currency,
            status=record.status.value,
            method_label=record.method_label,
            transaction_ref=record.transaction_ref,
            receipt_number=record.receipt_number,
            requested_by_id=record.requested_by_id,
            decided_by_id=record.decided_by_id,
            paid_at=record.paid_at,
        )

    def get(self, payout_id: uuid.UUID) -> PayoutRecord | None:
        row = Payout.objects.filter(id=payout_id).first()
        return _payout(row) if row else None

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        status: PayoutStatus | None = None,
    ) -> list[PayoutRecord]:
        rows = Payout.objects.order_by("requested_at")
        if tenant_id is not None:
            rows = rows.filter(tenant_id=tenant_id)
        if status is not None:
            rows = rows.filter(status=status.value)
        return [_payout(row) for row in rows]

    def update_status(self, record: PayoutRecord) -> None:
        Payout.objects.filter(id=record.id).update(
            status=record.status.value,
            transaction_ref=record.transaction_ref,
            receipt_number=record.receipt_number,
            decided_by_id=record.decided_by_id,
            paid_at=record.paid_at,
        )


class DjangoPayoutProofRepository:
    def create(self, record: PayoutProofRecord) -> None:
        try:
            PayoutProof.objects.create(
                payout_id=record.payout_id,
                object_ref=record.object_ref,
                content_type=record.content_type,
                checksum=record.checksum,
                uploaded_by_id=record.uploaded_by_id,
                agency_visible=bool(record.agency_visible),
                agency_visible_at=record.agency_visible_at,
                agency_visible_by=record.agency_visible_by,
            )
        except IntegrityError:
            return

    def get(self, payout_id: uuid.UUID) -> PayoutProofRecord | None:
        row = PayoutProof.objects.filter(payout_id=payout_id).first()
        if row is None:
            return None
        return _proof(row)

    def update(self, record: PayoutProofRecord) -> None:
        PayoutProof.objects.filter(payout_id=record.payout_id).update(
            object_ref=record.object_ref,
            content_type=record.content_type,
            checksum=record.checksum,
            uploaded_by_id=record.uploaded_by_id,
            agency_visible=bool(record.agency_visible),
            agency_visible_at=record.agency_visible_at,
            agency_visible_by=record.agency_visible_by,
        )


def _proof(row: PayoutProof) -> PayoutProofRecord:
    return PayoutProofRecord(
        payout_id=row.payout_id,
        object_ref=row.object_ref,
        content_type=row.content_type,
        checksum=row.checksum,
        uploaded_by_id=row.uploaded_by_id,
        agency_visible=bool(row.agency_visible),
        agency_visible_at=row.agency_visible_at,
        agency_visible_by=row.agency_visible_by,
    )


def _method(row: AgencyPayoutMethod) -> PayoutMethodRecord:
    return PayoutMethodRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        beneficiary_name=row.beneficiary_name,
        account_identifier=row.account_identifier,
        bank_name=row.bank_name,
        country=row.country,
        currency=row.currency,
        label=row.label,
        status=PayoutMethodStatus(row.status),
        is_default=bool(row.is_default),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class DjangoPayoutMethodRepository:
    def create(self, record: PayoutMethodRecord) -> None:
        AgencyPayoutMethod.objects.create(
            id=record.id,
            tenant_id=record.tenant_id,
            beneficiary_name=record.beneficiary_name,
            account_identifier=record.account_identifier,
            bank_name=record.bank_name,
            country=record.country,
            currency=record.currency,
            label=record.label,
            status=record.status.value,
            is_default=record.is_default,
        )

    def get(self, method_id: uuid.UUID) -> PayoutMethodRecord | None:
        row = AgencyPayoutMethod.objects.filter(id=method_id).first()
        return _method(row) if row else None

    def list_for_tenant(self, tenant_id: uuid.UUID) -> list[PayoutMethodRecord]:
        rows = AgencyPayoutMethod.objects.filter(tenant_id=tenant_id).order_by(
            "-is_default", "-created_at"
        )
        return [_method(row) for row in rows]

    def update(self, record: PayoutMethodRecord) -> None:
        AgencyPayoutMethod.objects.filter(id=record.id).update(
            beneficiary_name=record.beneficiary_name,
            account_identifier=record.account_identifier,
            bank_name=record.bank_name,
            country=record.country,
            currency=record.currency,
            label=record.label,
            status=record.status.value,
            is_default=record.is_default,
        )

    def clear_default(self, tenant_id: uuid.UUID) -> None:
        AgencyPayoutMethod.objects.filter(tenant_id=tenant_id, is_default=True).update(
            is_default=False
        )


class DjangoCommissionIdempotencyRepository:
    def get(self, actor_id: uuid.UUID, key: str) -> uuid.UUID | None:
        row = CommissionIdempotencyKey.objects.filter(actor_id=actor_id, key=key).first()
        return row.resource_id if row else None

    def create(self, actor_id: uuid.UUID, key: str, resource_id: uuid.UUID) -> None:
        try:
            CommissionIdempotencyKey.objects.create(
                actor_id=actor_id, key=key, resource_id=resource_id
            )
        except IntegrityError:
            return


def atomic():
    return transaction.atomic()
