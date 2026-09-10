from __future__ import annotations

import uuid

from shared_kernel.errors import DomainError
from tenant.recordings.domain import TenantArtifactRecord
from tenant.recordings.ports import TenantRecordingStore
from tenant.runtime.router import TenantRouter


class TenantRecordingService:
    def __init__(self, router: TenantRouter, store: TenantRecordingStore) -> None:
        self._router = router
        self._store = store

    def put_artifact(
        self, tenant_id: uuid.UUID, row: TenantArtifactRecord
    ) -> TenantArtifactRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_artifact(connection, row)
            stored = self._store.get_artifact(connection, row.artifact_id)
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def get_artifact(
        self, tenant_id: uuid.UUID, artifact_id: uuid.UUID
    ) -> TenantArtifactRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_artifact(connection, artifact_id)

    def list_artifacts(
        self,
        tenant_id: uuid.UUID,
        *,
        call_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[TenantArtifactRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_artifacts(
                connection, call_id=call_id, customer_id=customer_id
            )
