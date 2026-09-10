from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.recordings.domain.types import ArtifactKind, ArtifactStatus, GrantStatus


@dataclass(frozen=True, slots=True)
class ArtifactIndexRecord:
    artifact_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    call_id: uuid.UUID
    kind: ArtifactKind
    object_key: str
    checksum: str
    status: ArtifactStatus
    legal_hold: bool


@dataclass(frozen=True, slots=True)
class AccessGrantRecord:
    grant_id: uuid.UUID
    token_hash: str
    artifact_id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    call_id: uuid.UUID
    actor_id: uuid.UUID
    status: GrantStatus
    expires_at: datetime
    consumed_at: datetime | None = None


class ArtifactIndexRepository(Protocol):
    def get(self, artifact_id: uuid.UUID) -> ArtifactIndexRecord | None: ...
    def get_by_object_key(self, object_key: str) -> ArtifactIndexRecord | None: ...
    def save(self, record: ArtifactIndexRecord) -> ArtifactIndexRecord: ...
    def list_all(self) -> list[ArtifactIndexRecord]: ...


class IngestEventRepository(Protocol):
    def get(self, event_id: str) -> uuid.UUID | None: ...
    def save(self, event_id: str, artifact_id: uuid.UUID) -> None: ...


class AccessGrantRepository(Protocol):
    def save(self, record: AccessGrantRecord) -> AccessGrantRecord: ...
    def get_by_hash(self, token_hash: str) -> AccessGrantRecord | None: ...


class RecordingObjectStore(Protocol):
    def put(self, *, object_key: str, checksum: str, size_bytes: int) -> object: ...
    def exists(self, object_key: str) -> bool: ...
    def get(self, object_key: str) -> object | None: ...
    def list_keys(self) -> list[str]: ...
