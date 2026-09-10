from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from control_plane.telephony.domain.call_types import CallDirection, CallStatus


@dataclass(frozen=True, slots=True)
class TenantCallRecord:
    call_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    agent_id: uuid.UUID
    phone_number_id: uuid.UUID | None
    e164: str
    edge_call_id: str
    sip_call_id: str
    direction: CallDirection
    status: CallStatus
    billed_minutes: int
    duration_seconds: int
    end_reason: str
    started_at: datetime
    ended_at: datetime | None = None
    remote_e164: str = ""
    transfer_destination_id: uuid.UUID | None = None
    voicemail_status: str = ""


@dataclass(frozen=True, slots=True)
class TenantCallEventRecord:
    event_id: uuid.UUID
    call_id: uuid.UUID
    tenant_id: uuid.UUID
    event_type: str
    role: str
    reason: str
    created_at: datetime
