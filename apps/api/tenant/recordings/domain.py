from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from control_plane.recordings.domain.types import ArtifactKind, ArtifactStatus


@dataclass(frozen=True, slots=True)
class TenantArtifactRecord:
    artifact_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    call_id: uuid.UUID
    kind: ArtifactKind
    object_key: str
    content_type: str
    size_bytes: int
    checksum: str
    status: ArtifactStatus
    legal_hold: bool
    retention_until: datetime
    provider_ref: str
    created_at: datetime
    available_at: datetime | None = None
    deleted_at: datetime | None = None
