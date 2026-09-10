from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.audit.application.ports import AuditEventRecord, AuditRepository
from control_plane.audit.domain.policies import (
    assert_override_reason,
    redact_payload,
    severity_for,
)
from control_plane.identity.infrastructure.clock import SystemClock
from shared_kernel.http.correlation import get_correlation_id
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.audit")


@dataclass(frozen=True, slots=True)
class RecordAuditCommand:
    action: str
    entity_type: str
    entity_id: str = ""
    actor_id: uuid.UUID | None = None
    actor_role: str = ""
    tenant_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    reason: str = ""
    before_summary: str = ""
    after_summary: str = ""
    payload: dict | None = None
    ip: str = ""
    user_agent: str = ""


class RecordAudit:
    def __init__(self, events: AuditRepository, clock: SystemClock | None = None) -> None:
        self._events = events
        self._clock = clock or SystemClock()

    def execute(self, command: RecordAuditCommand) -> AuditEventRecord:
        action = command.action.strip()
        reason = assert_override_reason(action, command.reason)
        record = AuditEventRecord(
            id=new_uuid7(),
            actor_id=command.actor_id,
            actor_role=command.actor_role.strip()[:64],
            tenant_id=command.tenant_id,
            customer_id=command.customer_id,
            action=action,
            entity_type=command.entity_type.strip()[:64],
            entity_id=str(command.entity_id)[:64],
            severity=severity_for(action),
            correlation_id=get_correlation_id() or "",
            ip=command.ip.strip()[:64],
            user_agent=command.user_agent.strip()[:255],
            reason=reason,
            before_summary=command.before_summary.strip()[:255],
            after_summary=command.after_summary.strip()[:255],
            payload=redact_payload(command.payload),
            created_at=self._clock.now(),
        )
        self._events.append(record)
        log_event(
            logger,
            "audit.recorded",
            outcome="success",
            action=record.action,
            severity=record.severity.value,
            entity_type=record.entity_type,
            tenant_id=str(record.tenant_id) if record.tenant_id else None,
        )
        return record
