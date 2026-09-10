from __future__ import annotations

import uuid

from control_plane.audit.application.ports import AuditEventRecord, AuditSearchQuery
from control_plane.audit.domain.policies import assert_immutable
from control_plane.audit.domain.types import AuditSeverity
from control_plane.audit.models import AuditEvent


def _record(row: AuditEvent) -> AuditEventRecord:
    return AuditEventRecord(
        id=row.id,
        actor_id=row.actor_id,
        actor_role=row.actor_role,
        tenant_id=row.tenant_id,
        customer_id=row.customer_id,
        action=row.action,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        severity=AuditSeverity(row.severity),
        correlation_id=row.correlation_id,
        ip=row.ip,
        user_agent=row.user_agent,
        reason=row.reason,
        before_summary=row.before_summary,
        after_summary=row.after_summary,
        payload=row.payload if isinstance(row.payload, dict) else {},
        created_at=row.created_at,
    )


class DjangoAuditRepository:
    def append(self, record: AuditEventRecord) -> None:
        AuditEvent.objects.create(
            id=record.id,
            actor_id=record.actor_id,
            actor_role=record.actor_role,
            tenant_id=record.tenant_id,
            customer_id=record.customer_id,
            action=record.action,
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            severity=record.severity.value,
            correlation_id=record.correlation_id,
            ip=record.ip,
            user_agent=record.user_agent,
            reason=record.reason,
            before_summary=record.before_summary,
            after_summary=record.after_summary,
            payload=record.payload,
            created_at=record.created_at,
        )

    def get(self, event_id: uuid.UUID) -> AuditEventRecord | None:
        row = AuditEvent.objects.filter(id=event_id).first()
        return _record(row) if row else None

    def search(self, query: AuditSearchQuery) -> list[AuditEventRecord]:
        rows = AuditEvent.objects.all().order_by("-created_at")
        if query.actor_id is not None:
            rows = rows.filter(actor_id=query.actor_id)
        if query.action:
            rows = rows.filter(action=query.action)
        if query.entity_type:
            rows = rows.filter(entity_type=query.entity_type)
        if query.entity_id:
            rows = rows.filter(entity_id=query.entity_id)
        if query.tenant_id is not None:
            rows = rows.filter(tenant_id=query.tenant_id)
        if query.customer_id is not None:
            rows = rows.filter(customer_id=query.customer_id)
        if query.ip:
            rows = rows.filter(ip=query.ip)
        if query.severity is not None:
            rows = rows.filter(severity=query.severity.value)
        if query.since is not None:
            rows = rows.filter(created_at__gte=query.since)
        if query.until is not None:
            rows = rows.filter(created_at__lte=query.until)
        return [_record(row) for row in rows]

    def update(self, *_args, **_kwargs) -> None:
        assert_immutable()

    def delete(self, *_args, **_kwargs) -> None:
        assert_immutable()
