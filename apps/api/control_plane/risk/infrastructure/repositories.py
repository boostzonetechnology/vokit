from __future__ import annotations

import uuid

from control_plane.identity.models import Invitation, Membership
from control_plane.risk.application.ports import (
    RiskCaseRecord,
    RiskEventRecord,
    VerificationRecord,
)
from control_plane.risk.domain.types import RiskStatus, VerificationStatus
from control_plane.risk.models import RiskCase, RiskEvent, VerificationSubmission


def _case(row: RiskCase) -> RiskCaseRecord:
    return RiskCaseRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        customer_id=row.customer_id,
        status=RiskStatus(row.status),
        last_invoice_id=row.last_invoice_id,
        last_payment_id=row.last_payment_id,
        last_event_id=row.last_event_id,
        note=row.note,
        permanently_banned=bool(row.permanently_banned),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _event(row: RiskEvent) -> RiskEventRecord:
    return RiskEventRecord(
        processor=row.processor,
        event_id=row.event_id,
        customer_id=row.customer_id,
        kind=row.kind,
        status=row.status,
    )


def _verification(row: VerificationSubmission) -> VerificationRecord:
    return VerificationRecord(
        id=row.id,
        case_id=row.case_id,
        status=VerificationStatus(row.status),
        id_object_ref=row.id_object_ref,
        id_checksum=row.id_checksum,
        card_object_ref=row.card_object_ref,
        card_checksum=row.card_checksum,
        card_last4=row.card_last4,
    )


class DjangoRiskCaseRepository:
    def get(self, case_id: uuid.UUID) -> RiskCaseRecord | None:
        row = RiskCase.objects.filter(id=case_id).first()
        return _case(row) if row else None

    def get_for_customer(self, customer_id: uuid.UUID) -> RiskCaseRecord | None:
        row = RiskCase.objects.filter(customer_id=customer_id).first()
        return _case(row) if row else None

    def list(self, *, status: RiskStatus | None = None) -> list[RiskCaseRecord]:
        rows = RiskCase.objects.order_by("created_at")
        if status is not None:
            rows = rows.filter(status=status.value)
        return [_case(row) for row in rows]

    def upsert(self, record: RiskCaseRecord) -> None:
        RiskCase.objects.update_or_create(
            id=record.id,
            defaults={
                "tenant_id": record.tenant_id,
                "customer_id": record.customer_id,
                "status": record.status.value,
                "last_invoice_id": record.last_invoice_id,
                "last_payment_id": record.last_payment_id,
                "last_event_id": record.last_event_id,
                "note": record.note[:255],
                "permanently_banned": record.permanently_banned,
            },
        )


class DjangoRiskEventRepository:
    def get(self, processor: str, event_id: str) -> RiskEventRecord | None:
        row = RiskEvent.objects.filter(processor=processor, event_id=event_id).first()
        return _event(row) if row else None

    def create(self, record: RiskEventRecord) -> None:
        RiskEvent.objects.create(
            processor=record.processor,
            event_id=record.event_id,
            customer_id=record.customer_id,
            kind=record.kind,
            status=record.status,
        )

    def list(self, *, kind: str | None = None) -> list[RiskEventRecord]:
        rows = RiskEvent.objects.order_by("created_at")
        if kind:
            rows = rows.filter(kind=kind)
        return [_event(row) for row in rows]


class DjangoVerificationRepository:
    def create(self, record: VerificationRecord) -> None:
        VerificationSubmission.objects.create(
            id=record.id,
            case_id=record.case_id,
            status=record.status.value,
            id_object_ref=record.id_object_ref,
            id_checksum=record.id_checksum,
            card_object_ref=record.card_object_ref,
            card_checksum=record.card_checksum,
            card_last4=record.card_last4,
        )

    def latest_for_case(self, case_id: uuid.UUID) -> VerificationRecord | None:
        row = (
            VerificationSubmission.objects.filter(case_id=case_id)
            .order_by("-created_at")
            .first()
        )
        return _verification(row) if row else None


class DjangoCustomerEmailLookup:
    def emails_for_customer(self, customer_id: uuid.UUID) -> list[str]:
        emails: list[str] = []
        for row in Membership.objects.filter(customer_id=customer_id).select_related("user"):
            emails.append(row.user.email)
        for row in Invitation.objects.filter(customer_id=customer_id):
            emails.append(row.email)
        seen: set[str] = set()
        unique: list[str] = []
        for email in emails:
            normalized = email.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(normalized)
        return unique
