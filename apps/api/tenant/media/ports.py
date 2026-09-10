from __future__ import annotations

import uuid
from typing import Protocol

from tenant.media.domain import TransferDestinationRecord, VoicemailMessageRecord
from tenant.runtime.ports import TenantConnection


class TenantMediaStore(Protocol):
    def put_destination(
        self, connection: TenantConnection, row: TransferDestinationRecord
    ) -> None: ...

    def get_destination(
        self, connection: TenantConnection, destination_id: uuid.UUID
    ) -> TransferDestinationRecord | None: ...

    def list_destinations(
        self,
        connection: TenantConnection,
        *,
        customer_id: uuid.UUID | None = None,
    ) -> list[TransferDestinationRecord]: ...

    def put_voicemail(
        self, connection: TenantConnection, row: VoicemailMessageRecord
    ) -> None: ...

    def get_voicemail(
        self, connection: TenantConnection, message_id: uuid.UUID
    ) -> VoicemailMessageRecord | None: ...

    def list_voicemail(
        self,
        connection: TenantConnection,
        *,
        call_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> list[VoicemailMessageRecord]: ...
