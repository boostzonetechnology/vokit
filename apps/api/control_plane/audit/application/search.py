from __future__ import annotations

from control_plane.audit.application.ports import (
    AuditEventRecord,
    AuditRepository,
    AuditSearchQuery,
)


class SearchAudit:
    def __init__(self, events: AuditRepository) -> None:
        self._events = events

    def execute(self, query: AuditSearchQuery) -> list[AuditEventRecord]:
        return self._events.search(query)
