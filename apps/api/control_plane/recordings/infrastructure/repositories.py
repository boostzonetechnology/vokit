from __future__ import annotations

import uuid

from control_plane.recordings.application.ports import (
    AccessGrantRecord,
    ArtifactIndexRecord,
)
from control_plane.recordings.domain.types import ArtifactKind, ArtifactStatus, GrantStatus
from control_plane.recordings.models import (
    RecordingAccessGrant,
    RecordingArtifactIndex,
    RecordingIngestEvent,
)


def _to_index(row: RecordingArtifactIndex) -> ArtifactIndexRecord:
    return ArtifactIndexRecord(
        artifact_id=row.id,
        tenant_id=row.tenant_id,
        customer_id=row.customer_id,
        call_id=row.call_id,
        kind=ArtifactKind(row.kind),
        object_key=row.object_key,
        checksum=row.checksum,
        status=ArtifactStatus(row.status),
        legal_hold=row.legal_hold,
    )


def _to_grant(row: RecordingAccessGrant) -> AccessGrantRecord:
    return AccessGrantRecord(
        grant_id=row.id,
        token_hash=row.token_hash,
        artifact_id=row.artifact_id,
        tenant_id=row.tenant_id,
        customer_id=row.customer_id,
        call_id=row.call_id,
        actor_id=row.actor_id,
        status=GrantStatus(row.status),
        expires_at=row.expires_at,
        consumed_at=row.consumed_at,
    )


class DjangoArtifactIndexRepository:
    def get(self, artifact_id: uuid.UUID) -> ArtifactIndexRecord | None:
        row = RecordingArtifactIndex.objects.filter(id=artifact_id).first()
        return _to_index(row) if row else None

    def get_by_object_key(self, object_key: str) -> ArtifactIndexRecord | None:
        row = RecordingArtifactIndex.objects.filter(object_key=object_key).first()
        return _to_index(row) if row else None

    def save(self, record: ArtifactIndexRecord) -> ArtifactIndexRecord:
        RecordingArtifactIndex.objects.update_or_create(
            id=record.artifact_id,
            defaults={
                "tenant_id": record.tenant_id,
                "customer_id": record.customer_id,
                "call_id": record.call_id,
                "kind": record.kind.value,
                "object_key": record.object_key,
                "checksum": record.checksum,
                "status": record.status.value,
                "legal_hold": record.legal_hold,
            },
        )
        stored = RecordingArtifactIndex.objects.get(id=record.artifact_id)
        return _to_index(stored)

    def list_all(self) -> list[ArtifactIndexRecord]:
        return [_to_index(row) for row in RecordingArtifactIndex.objects.all()]


class DjangoIngestEventRepository:
    def get(self, event_id: str) -> uuid.UUID | None:
        row = RecordingIngestEvent.objects.filter(event_id=event_id).first()
        return row.artifact_id if row else None

    def save(self, event_id: str, artifact_id: uuid.UUID) -> None:
        RecordingIngestEvent.objects.update_or_create(
            event_id=event_id,
            defaults={"artifact_id": artifact_id},
        )


class DjangoAccessGrantRepository:
    def save(self, record: AccessGrantRecord) -> AccessGrantRecord:
        RecordingAccessGrant.objects.update_or_create(
            id=record.grant_id,
            defaults={
                "token_hash": record.token_hash,
                "artifact_id": record.artifact_id,
                "tenant_id": record.tenant_id,
                "customer_id": record.customer_id,
                "call_id": record.call_id,
                "actor_id": record.actor_id,
                "status": record.status.value,
                "expires_at": record.expires_at,
                "consumed_at": record.consumed_at,
            },
        )
        stored = RecordingAccessGrant.objects.get(id=record.grant_id)
        return _to_grant(stored)

    def get_by_hash(self, token_hash: str) -> AccessGrantRecord | None:
        row = RecordingAccessGrant.objects.filter(token_hash=token_hash).first()
        return _to_grant(row) if row else None
