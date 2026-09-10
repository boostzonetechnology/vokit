from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class JobContext:
    tenant_id: uuid.UUID
    correlation_id: str
    actor_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None


@dataclass(frozen=True, slots=True)
class IsolationRecord:
    object_id: uuid.UUID
    tenant_id: uuid.UUID
    payload: str
    created_at: datetime | None = None
