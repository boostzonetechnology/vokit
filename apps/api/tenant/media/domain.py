from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from control_plane.telephony.domain.destinations import DestinationKind, DestinationStatus
from control_plane.telephony.domain.voicemail import VoicemailDirection, VoicemailStatus


@dataclass(frozen=True, slots=True)
class TransferMemberRecord:
    kind: DestinationKind
    target: str
    label: str = ""


@dataclass(frozen=True, slots=True)
class TransferDestinationRecord:
    destination_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    kind: DestinationKind
    label: str
    target: str
    members: tuple[TransferMemberRecord, ...]
    no_answer_seconds: int
    status: DestinationStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class VoicemailMessageRecord:
    message_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    agent_id: uuid.UUID
    call_id: uuid.UUID
    direction: VoicemailDirection
    status: VoicemailStatus
    object_ref: str
    duration_seconds: int
    created_at: datetime
    updated_at: datetime
