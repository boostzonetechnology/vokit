from __future__ import annotations

import uuid
from typing import Protocol

from tenant.recordings.domain import TenantArtifactRecord
from tenant.runtime.ports import TenantConnection


class TenantRecordingStore(Protocol):
    def put_artifact(
        self, connection: TenantConnection, row: TenantArtifactRecord
    ) -> None: ...

    def get_artifact(
        self, connection: TenantConnection, artifact_id: uuid.UUID
    ) -> TenantArtifactRecord | None: ...

    def list_artifacts(
        self,
        connection: TenantConnection,
        *,
        call_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantArtifactRecord]: ...
