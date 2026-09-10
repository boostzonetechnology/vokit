from __future__ import annotations

import uuid
from typing import Protocol

from tenant.calls.domain import TenantCallEventRecord, TenantCallRecord
from tenant.runtime.ports import TenantConnection


class TenantCallStore(Protocol):
    def put_call(self, connection: TenantConnection, row: TenantCallRecord) -> None: ...

    def get_call(
        self, connection: TenantConnection, call_id: uuid.UUID
    ) -> TenantCallRecord | None: ...

    def get_call_by_edge(
        self, connection: TenantConnection, edge_call_id: str
    ) -> TenantCallRecord | None: ...

    def put_call_event(
        self, connection: TenantConnection, row: TenantCallEventRecord
    ) -> None: ...

    def list_calls(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
    ) -> list[TenantCallRecord]: ...
