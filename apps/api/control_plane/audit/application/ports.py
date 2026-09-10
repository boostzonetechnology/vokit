from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.audit.domain.types import AuditSeverity


@dataclass(frozen=True, slots=True)
class AuditEventRecord:
    id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_role: str
    tenant_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: str
    severity: AuditSeverity
    correlation_id: str
    ip: str
    user_agent: str
    reason: str
    before_summary: str
    after_summary: str
    payload: dict
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuditSearchQuery:
    actor_id: uuid.UUID | None = None
    action: str = ""
    entity_type: str = ""
    entity_id: str = ""
    tenant_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    ip: str = ""
    severity: AuditSeverity | None = None
    since: datetime | None = None
    until: datetime | None = None


class AuditRepository(Protocol):
    def append(self, record: AuditEventRecord) -> None: ...
    def get(self, event_id: uuid.UUID) -> AuditEventRecord | None: ...
    def search(self, query: AuditSearchQuery) -> list[AuditEventRecord]: ...
