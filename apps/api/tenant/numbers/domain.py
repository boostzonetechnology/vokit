from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from control_plane.telephony.domain.types import AssignmentStatus


@dataclass(frozen=True, slots=True)
class NumberAssignmentRecord:
    assignment_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    agent_id: uuid.UUID
    phone_number_id: uuid.UUID
    e164: str
    status: AssignmentStatus
    invoice_id: uuid.UUID | None
    assigned_at: datetime
    released_at: datetime | None = None
