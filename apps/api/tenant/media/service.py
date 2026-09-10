from __future__ import annotations

import uuid

from shared_kernel.errors import DomainError
from tenant.media.domain import TransferDestinationRecord, VoicemailMessageRecord
from tenant.media.ports import TenantMediaStore
from tenant.runtime.router import TenantRouter


class TenantMediaService:
    def __init__(self, router: TenantRouter, store: TenantMediaStore) -> None:
        self._router = router
        self._store = store

    def put_destination(
        self, tenant_id: uuid.UUID, row: TransferDestinationRecord
    ) -> TransferDestinationRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_destination(connection, row)
            stored = self._store.get_destination(connection, row.destination_id)
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def get_destination(
        self, tenant_id: uuid.UUID, destination_id: uuid.UUID
    ) -> TransferDestinationRecord | None:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.get_destination(connection, destination_id)

    def list_destinations(
        self,
        tenant_id: uuid.UUID,
        *,
        customer_id: uuid.UUID | None = None,
    ) -> list[TransferDestinationRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_destinations(connection, customer_id=customer_id)

    def put_voicemail(
        self, tenant_id: uuid.UUID, row: VoicemailMessageRecord
    ) -> VoicemailMessageRecord:
        with self._router.connection_for_tenant(tenant_id) as connection:
            self._store.put_voicemail(connection, row)
            stored = self._store.get_voicemail(connection, row.message_id)
        if stored is None:
            raise DomainError(
                "tenant_write_failed",
                "Tenant write could not be verified.",
                http_status=503,
            )
        return stored

    def list_voicemail(
        self,
        tenant_id: uuid.UUID,
        *,
        call_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[VoicemailMessageRecord]:
        with self._router.connection_for_tenant(tenant_id) as connection:
            return self._store.list_voicemail(
                connection, call_id=call_id, customer_id=customer_id
            )
