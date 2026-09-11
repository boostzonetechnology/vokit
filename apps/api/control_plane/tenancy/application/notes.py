from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from control_plane.audit.application.record import RecordAudit, RecordAuditCommand
from control_plane.tenancy.application.ports import Clock, TenantRepository
from control_plane.tenancy.models import AgencyNote
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7


@dataclass(frozen=True, slots=True)
class AgencyNoteRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    body: str
    risk_flag: bool
    created_by_id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CreateAgencyNoteCommand:
    tenant_id: uuid.UUID
    body: str
    risk_flag: bool
    actor_id: uuid.UUID
    actor_role: str = ""


class CreateAgencyNote:
    def __init__(
        self,
        tenants: TenantRepository,
        audit: RecordAudit,
        clock: Clock,
    ) -> None:
        self._tenants = tenants
        self._audit = audit
        self._clock = clock

    def execute(self, command: CreateAgencyNoteCommand) -> AgencyNoteRecord:
        if self._tenants.get(command.tenant_id) is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        body = command.body.strip()
        if not body:
            raise DomainError("validation_error", "body is required.")
        if len(body) > 2000:
            raise DomainError("validation_error", "body is too long.")
        note_id = new_uuid7()
        row = AgencyNote.objects.create(
            id=note_id,
            tenant_id=command.tenant_id,
            body=body[:2000],
            risk_flag=bool(command.risk_flag),
            created_by_id=command.actor_id,
        )
        self._audit.execute(
            RecordAuditCommand(
                action="agency.note.created",
                entity_type="agency_note",
                entity_id=str(note_id),
                actor_id=command.actor_id,
                actor_role=command.actor_role,
                tenant_id=command.tenant_id,
                after_summary="risk" if command.risk_flag else "note",
            )
        )
        return AgencyNoteRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            body=row.body,
            risk_flag=row.risk_flag,
            created_by_id=row.created_by_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class ListAgencyNotes:
    def __init__(self, tenants: TenantRepository) -> None:
        self._tenants = tenants

    def execute(self, tenant_id: uuid.UUID) -> list[AgencyNoteRecord]:
        if self._tenants.get(tenant_id) is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        rows = AgencyNote.objects.filter(tenant_id=tenant_id).order_by("-created_at")
        return [
            AgencyNoteRecord(
                id=row.id,
                tenant_id=row.tenant_id,
                body=row.body,
                risk_flag=row.risk_flag,
                created_by_id=row.created_by_id,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]
