from __future__ import annotations

import uuid
from contextlib import AbstractContextManager
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from control_plane.telephony.application.ports import PhoneNumberRecord, ReservationRecord
from control_plane.telephony.application.session import CallIndexRecord
from control_plane.telephony.domain.call_types import CallDirection, CallStatus, TransferStatus
from control_plane.telephony.domain.types import NumberStatus, ReservationStatus
from control_plane.telephony.models import (
    CallIndex,
    PhoneNumber,
    PhoneNumberReservation,
    TrainingProposal,
    TrainingSessionIndex,
    TransferDestinationIndex,
)
from shared_kernel.money import Money


def _capabilities(raw: str) -> tuple[str, ...]:
    return tuple(part for part in (raw or "").split(",") if part)


def _to_number(row: PhoneNumber) -> PhoneNumberRecord:
    return PhoneNumberRecord(
        id=row.id,
        e164=row.e164,
        country=row.country,
        area=row.area,
        capabilities=_capabilities(row.capabilities),
        provider=row.provider,
        provider_ref=row.provider_ref,
        status=NumberStatus(row.status),
        monthly_cost=Money(int(row.monthly_cost_minor), row.currency),
        assigned_tenant_id=row.assigned_tenant_id,
        assigned_customer_id=row.assigned_customer_id,
        assigned_agent_id=row.assigned_agent_id,
        reservation_id=row.reservation_id,
        reserved_until=row.reserved_until,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_reservation(row: PhoneNumberReservation) -> ReservationRecord:
    return ReservationRecord(
        id=row.id,
        number_id=row.number_id,
        tenant_id=row.tenant_id,
        customer_id=row.customer_id,
        agent_id=row.agent_id,
        status=ReservationStatus(row.status),
        expires_at=row.expires_at,
        created_at=row.created_at,
    )


class DjangoPhoneNumberRepository:
    def transaction(self) -> AbstractContextManager[None]:
        return transaction.atomic()

    def get(self, number_id: uuid.UUID) -> PhoneNumberRecord | None:
        row = PhoneNumber.objects.filter(id=number_id).first()
        return _to_number(row) if row else None

    def get_by_e164(self, e164: str) -> PhoneNumberRecord | None:
        row = PhoneNumber.objects.filter(e164=e164).first()
        return _to_number(row) if row else None

    def list(
        self,
        *,
        status: NumberStatus | None = None,
        country: str = "",
        area: str = "",
        capability: str = "",
        tenant_id: uuid.UUID | None = None,
    ) -> list[PhoneNumberRecord]:
        rows = PhoneNumber.objects.all()
        if status is not None:
            rows = rows.filter(status=status.value)
        if country.strip():
            rows = rows.filter(country__iexact=country.strip())
        if area.strip():
            rows = rows.filter(area=area.strip())
        if capability.strip():
            rows = rows.filter(capabilities__icontains=capability.strip().lower())
        if tenant_id is not None:
            rows = rows.filter(assigned_tenant_id=tenant_id)
        return [_to_number(row) for row in rows.order_by("e164")]

    def save(self, record: PhoneNumberRecord) -> PhoneNumberRecord:
        PhoneNumber.objects.update_or_create(
            id=record.id,
            defaults={
                "e164": record.e164,
                "country": record.country,
                "area": record.area,
                "capabilities": ",".join(record.capabilities),
                "provider": record.provider,
                "provider_ref": record.provider_ref,
                "status": record.status.value,
                "monthly_cost_minor": record.monthly_cost.minor_units,
                "currency": record.monthly_cost.currency,
                "assigned_tenant_id": record.assigned_tenant_id,
                "assigned_customer_id": record.assigned_customer_id,
                "assigned_agent_id": record.assigned_agent_id,
                "reservation_id": record.reservation_id,
                "reserved_until": record.reserved_until,
            },
        )
        stored = PhoneNumber.objects.get(id=record.id)
        return _to_number(stored)

    def lock(self, number_id: uuid.UUID) -> PhoneNumberRecord | None:
        row = PhoneNumber.objects.select_for_update().filter(id=number_id).first()
        return _to_number(row) if row else None


class DjangoReservationRepository:
    def get(self, reservation_id: uuid.UUID) -> ReservationRecord | None:
        row = PhoneNumberReservation.objects.filter(id=reservation_id).first()
        return _to_reservation(row) if row else None

    def active_for_number(self, number_id: uuid.UUID) -> ReservationRecord | None:
        now = timezone.now()
        row = (
            PhoneNumberReservation.objects.filter(
                number_id=number_id,
                status=ReservationStatus.ACTIVE.value,
                expires_at__gt=now,
            )
            .order_by("-created_at")
            .first()
        )
        return _to_reservation(row) if row else None

    def save(self, record: ReservationRecord) -> ReservationRecord:
        PhoneNumberReservation.objects.update_or_create(
            id=record.id,
            defaults={
                "number_id": record.number_id,
                "tenant_id": record.tenant_id,
                "customer_id": record.customer_id,
                "agent_id": record.agent_id,
                "status": record.status.value,
                "expires_at": record.expires_at,
            },
        )
        return _to_reservation(PhoneNumberReservation.objects.get(id=record.id))

    def list_expired(self, now: datetime) -> list[ReservationRecord]:
        rows = PhoneNumberReservation.objects.filter(
            status=ReservationStatus.ACTIVE.value,
            expires_at__lte=now,
        )
        return [_to_reservation(row) for row in rows]


class DjangoCallIndexRepository:
    def get_by_edge(self, edge_call_id: str) -> CallIndexRecord | None:
        row = CallIndex.objects.filter(edge_call_id=edge_call_id).first()
        return _to_call(row) if row else None

    def save(self, record: CallIndexRecord) -> CallIndexRecord:
        CallIndex.objects.update_or_create(
            id=record.call_id,
            defaults={
                "tenant_id": record.tenant_id,
                "customer_id": record.customer_id,
                "agent_id": record.agent_id,
                "edge_call_id": record.edge_call_id,
                "e164": record.e164,
                "direction": record.direction.value,
                "status": record.status.value,
                "transfer_status": record.transfer_status.value,
                "billed_minutes": record.billed_minutes,
                "ended_at": record.ended_at,
                "remote_e164": record.remote_e164,
                "transfer_destination_id": record.transfer_destination_id,
                "voicemail_status": record.voicemail_status,
                "hunt_index": record.hunt_index,
            },
        )
        return _to_call(CallIndex.objects.get(id=record.call_id))

    def get(self, call_id: uuid.UUID) -> CallIndexRecord | None:
        row = CallIndex.objects.filter(id=call_id).first()
        return _to_call(row) if row else None

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[CallIndexRecord]:
        rows = CallIndex.objects.all()
        if tenant_id is not None:
            rows = rows.filter(tenant_id=tenant_id)
        if customer_id is not None:
            rows = rows.filter(customer_id=customer_id)
        return [_to_call(row) for row in rows.order_by("-created_at")]


class DjangoTransferIndexRepository:
    def get(self, destination_id: uuid.UUID):
        return TransferDestinationIndex.objects.filter(id=destination_id).first()

    def save(
        self,
        *,
        destination_id: uuid.UUID,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        kind: str,
        label: str,
        status: str,
        platform_disabled: bool | None = None,
    ) -> TransferDestinationIndex:
        defaults = {
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "kind": kind,
            "label": label,
            "status": status,
        }
        if platform_disabled is not None:
            defaults["platform_disabled"] = platform_disabled
        row, _created = TransferDestinationIndex.objects.update_or_create(
            id=destination_id,
            defaults=defaults,
        )
        return row

    def list(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[TransferDestinationIndex]:
        rows = TransferDestinationIndex.objects.all()
        if tenant_id is not None:
            rows = rows.filter(tenant_id=tenant_id)
        if customer_id is not None:
            rows = rows.filter(customer_id=customer_id)
        return list(rows.order_by("label"))


class DjangoTrainingProposalRepository:
    def create(self, session_id: uuid.UUID, kind: str, name: str, scope: str) -> str:
        row = TrainingProposal.objects.create(
            session_id=session_id,
            kind=(kind or "instruction")[:32],
            name=(name or "proposal")[:128],
            scope=(scope or "")[:32],
        )
        return str(row.id)

    def confirm(self, session_id: uuid.UUID) -> int:
        return TrainingProposal.objects.filter(
            session_id=session_id, status="proposed"
        ).update(status="confirmed")


class DjangoTrainingSessionIndex:
    def save(
        self,
        *,
        session_id: uuid.UUID,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> None:
        TrainingSessionIndex.objects.update_or_create(
            session_id=session_id,
            defaults={
                "tenant_id": tenant_id,
                "customer_id": customer_id,
                "agent_id": agent_id,
            },
        )

    def get(self, session_id: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID] | None:
        row = TrainingSessionIndex.objects.filter(session_id=session_id).first()
        if row is None:
            return None
        return row.tenant_id, row.agent_id


def _to_call(row: CallIndex) -> CallIndexRecord:
    return CallIndexRecord(
        call_id=row.id,
        tenant_id=row.tenant_id,
        customer_id=row.customer_id,
        agent_id=row.agent_id,
        edge_call_id=row.edge_call_id,
        e164=row.e164,
        direction=CallDirection(row.direction),
        status=CallStatus(row.status),
        transfer_status=TransferStatus(row.transfer_status),
        billed_minutes=row.billed_minutes,
        created_at=row.created_at,
        ended_at=row.ended_at,
        remote_e164=row.remote_e164,
        transfer_destination_id=row.transfer_destination_id,
        voicemail_status=row.voicemail_status,
        hunt_index=row.hunt_index,
    )
