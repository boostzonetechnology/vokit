from __future__ import annotations

import uuid
from typing import Protocol

from tenant.numbers.domain import NumberAssignmentRecord
from tenant.runtime.ports import TenantConnection


class TenantNumberStore(Protocol):
    def put_assignment(
        self, connection: TenantConnection, row: NumberAssignmentRecord
    ) -> None: ...

    def get_assignment(
        self, connection: TenantConnection, assignment_id: uuid.UUID
    ) -> NumberAssignmentRecord | None: ...

    def active_for_number(
        self, connection: TenantConnection, phone_number_id: uuid.UUID
    ) -> NumberAssignmentRecord | None: ...

    def list_assignments(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
    ) -> list[NumberAssignmentRecord]: ...
