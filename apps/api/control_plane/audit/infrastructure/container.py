from __future__ import annotations

from control_plane.audit.application.record import RecordAudit
from control_plane.audit.application.search import SearchAudit
from control_plane.audit.infrastructure.repositories import DjangoAuditRepository
from control_plane.identity.infrastructure.clock import SystemClock


def audit_events() -> DjangoAuditRepository:
    return DjangoAuditRepository()


def record_audit() -> RecordAudit:
    return RecordAudit(audit_events(), SystemClock())


def search_audit() -> SearchAudit:
    return SearchAudit(audit_events())
