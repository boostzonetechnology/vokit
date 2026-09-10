from __future__ import annotations

import logging
import secrets
import uuid
from dataclasses import dataclass, replace
from datetime import timedelta

from control_plane.ops.application.live_flags import assert_recordings_live
from control_plane.recordings.application.ports import (
    AccessGrantRecord,
    AccessGrantRepository,
    ArtifactIndexRecord,
    ArtifactIndexRepository,
    IngestEventRepository,
    RecordingObjectStore,
)
from control_plane.recordings.domain.policies import (
    assert_can_delete,
    assert_checksum,
    assert_content_type,
    assert_kind,
    assert_ready_for_access,
    assert_same_scope,
    assert_size,
    hash_token,
    next_status_after_hold,
    object_key,
    retention_until,
)
from control_plane.recordings.domain.types import ArtifactKind, ArtifactStatus, GrantStatus
from control_plane.telephony.application.session import CallIndexRepository
from control_plane.tenancy.application.ports import Clock
from providers.recordings.memory import RecordingStoreUnavailable
from shared_kernel.errors import DomainError
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event
from tenant.media.service import TenantMediaService
from tenant.recordings.domain import TenantArtifactRecord
from tenant.recordings.service import TenantRecordingService

logger = logging.getLogger("vokit.recordings")


@dataclass(frozen=True, slots=True)
class IngestCommand:
    event_id: str
    edge_call_id: str
    call_id: str
    artifact_id: str
    kind: str
    content_type: str
    size_bytes: object
    checksum: str
    provider_ref: str = ""
    tenant_id: str = ""


class RecordingControl:
    def __init__(
        self,
        calls: CallIndexRepository,
        artifacts: TenantRecordingService,
        media: TenantMediaService,
        index: ArtifactIndexRepository,
        events: IngestEventRepository,
        grants: AccessGrantRepository,
        store: RecordingObjectStore,
        clock: Clock,
        *,
        retention_days: int,
        access_ttl_seconds: int,
        public_base_url: str,
    ) -> None:
        self._calls = calls
        self._artifacts = artifacts
        self._media = media
        self._index = index
        self._events = events
        self._grants = grants
        self._store = store
        self._clock = clock
        self._retention_days = retention_days
        self._ttl = access_ttl_seconds
        self._public_base = public_base_url.rstrip("/")

    def ingest(self, command: IngestCommand) -> dict[str, object]:
        event_id = (command.event_id or "").strip()
        if not event_id:
            raise DomainError("validation_error", "event_id is required.")
        replay = self._events.get(event_id)
        if replay is not None:
            indexed = self._index.get(replay)
            if indexed is None:
                raise DomainError("not_found", "Resource not found.", http_status=404)
            if indexed.status in {ArtifactStatus.ANNOUNCED, ArtifactStatus.VERIFYING}:
                indexed = self._verify(indexed)
            return self._payload(indexed)
        assert_recordings_live()
        call = self._resolve_call(command)
        if command.tenant_id.strip():
            try:
                claimed = uuid.UUID(command.tenant_id.strip())
            except (ValueError, TypeError, AttributeError):
                claimed = None
            if claimed is not None and claimed != call.tenant_id:
                log_event(
                    logger,
                    "recording.ingest.forged_tenant",
                    outcome="ignored",
                    call_id=str(call.call_id),
                )
        artifact_id = self._parse_optional_id(command.artifact_id) or new_uuid7()
        existing = self._index.get(artifact_id)
        if existing is not None:
            if command.checksum.strip():
                incoming = assert_checksum(command.checksum)
                if incoming != existing.checksum:
                    raise DomainError(
                        "conflict_state",
                        "Recording objects are immutable.",
                        http_status=409,
                    )
            self._events.save(event_id, existing.artifact_id)
            if existing.status in {ArtifactStatus.ANNOUNCED, ArtifactStatus.VERIFYING}:
                existing = self._verify(existing)
            return self._payload(existing)
        kind = assert_kind(command.kind)
        checksum = assert_checksum(command.checksum)
        content_type = assert_content_type(command.content_type)
        size_bytes = assert_size(command.size_bytes)
        key = object_key(
            tenant_id=call.tenant_id, call_id=call.call_id, artifact_id=artifact_id
        )
        now = self._clock.now()
        row = TenantArtifactRecord(
            artifact_id=artifact_id,
            tenant_id=call.tenant_id,
            customer_id=call.customer_id,
            call_id=call.call_id,
            kind=kind,
            object_key=key,
            content_type=content_type,
            size_bytes=size_bytes,
            checksum=checksum,
            status=ArtifactStatus.VERIFYING,
            legal_hold=False,
            retention_until=retention_until(now, days=self._retention_days),
            provider_ref=(command.provider_ref or "").strip()[:128],
            created_at=now,
        )
        stored = self._artifacts.put_artifact(call.tenant_id, row)
        indexed = self._index.save(self._to_index(stored))
        self._events.save(event_id, artifact_id)
        indexed = self._verify(indexed)
        if kind is ArtifactKind.VOICEMAIL:
            self._link_voicemail(call, key)
        log_event(
            logger,
            "recording.ingested",
            outcome="success",
            tenant_id=str(call.tenant_id),
            call_id=str(call.call_id),
            artifact_id=str(artifact_id),
            status=indexed.status.value,
        )
        return self._payload(indexed)

    def verify(self, artifact_id: uuid.UUID) -> dict[str, object]:
        indexed = self._require_index(artifact_id)
        return self._payload(self._verify(indexed))

    def grant_access(
        self,
        *,
        call_id: uuid.UUID,
        artifact_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_tenant_id: uuid.UUID | None,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> dict[str, object]:
        assert_recordings_live()
        indexed = self._authorized_artifact(
            call_id=call_id,
            artifact_id=artifact_id,
            actor_tenant_id=actor_tenant_id,
            actor_customer_id=actor_customer_id,
            privileged=privileged,
        )
        assert_ready_for_access(indexed.status)
        now = self._clock.now()
        token = secrets.token_urlsafe(32)
        grant = self._grants.save(
            AccessGrantRecord(
                grant_id=new_uuid7(),
                token_hash=hash_token(token),
                artifact_id=indexed.artifact_id,
                tenant_id=indexed.tenant_id,
                customer_id=indexed.customer_id,
                call_id=indexed.call_id,
                actor_id=actor_id,
                status=GrantStatus.ISSUED,
                expires_at=now + timedelta(seconds=self._ttl),
            )
        )
        log_event(
            logger,
            "recording.access.granted",
            outcome="success",
            tenant_id=str(indexed.tenant_id),
            call_id=str(indexed.call_id),
            artifact_id=str(indexed.artifact_id),
            actor_id=str(actor_id),
        )
        return {
            "token": token,
            "expires_at": grant.expires_at.isoformat(),
            "url": f"{self._public_base}/stream?token={token}",
            "artifact_id": str(indexed.artifact_id),
        }

    def validate_access(self, token: str) -> dict[str, object]:
        raw = (token or "").strip()
        if not raw:
            raise DomainError("unauthenticated", "Authentication required.", http_status=401)
        grant = self._grants.get_by_hash(hash_token(raw))
        if grant is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        now = self._clock.now()
        if grant.status is GrantStatus.CONSUMED:
            raise DomainError("access_replayed", "Access token was already used.", http_status=401)
        if grant.status is GrantStatus.EXPIRED or now >= grant.expires_at:
            self._grants.save(replace(grant, status=GrantStatus.EXPIRED))
            raise DomainError("access_expired", "Access token expired.", http_status=401)
        indexed = self._require_index(grant.artifact_id)
        assert_same_scope(
            tenant_id=grant.tenant_id,
            customer_id=grant.customer_id,
            call_id=grant.call_id,
            expected_tenant=indexed.tenant_id,
            expected_customer=indexed.customer_id,
            expected_call=indexed.call_id,
        )
        assert_ready_for_access(indexed.status)
        self._grants.save(
            replace(grant, status=GrantStatus.CONSUMED, consumed_at=now)
        )
        log_event(
            logger,
            "recording.access.consumed",
            outcome="success",
            tenant_id=str(indexed.tenant_id),
            artifact_id=str(indexed.artifact_id),
        )
        return {
            "ok": True,
            "object_key": indexed.object_key,
            "artifact_id": str(indexed.artifact_id),
            "call_id": str(indexed.call_id),
        }

    def set_hold(
        self,
        *,
        call_id: uuid.UUID,
        artifact_id: uuid.UUID,
        hold: bool,
        actor_tenant_id: uuid.UUID | None,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> dict[str, object]:
        indexed = self._authorized_artifact(
            call_id=call_id,
            artifact_id=artifact_id,
            actor_tenant_id=actor_tenant_id,
            actor_customer_id=actor_customer_id,
            privileged=privileged,
        )
        status = next_status_after_hold(legal_hold=hold, status=indexed.status)
        row = self._artifacts.get_artifact(indexed.tenant_id, indexed.artifact_id)
        if row is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        stored = self._artifacts.put_artifact(
            indexed.tenant_id,
            replace(row, legal_hold=hold, status=status),
        )
        updated = self._index.save(self._to_index(stored))
        log_event(
            logger,
            "recording.hold.changed",
            outcome="success",
            artifact_id=str(updated.artifact_id),
            legal_hold=hold,
        )
        return self._payload(updated)

    def delete(
        self,
        *,
        call_id: uuid.UUID,
        artifact_id: uuid.UUID,
        confirm: bool,
        actor_tenant_id: uuid.UUID | None,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> dict[str, object]:
        if not confirm:
            raise DomainError("validation_error", "confirm is required.")
        indexed = self._authorized_artifact(
            call_id=call_id,
            artifact_id=artifact_id,
            actor_tenant_id=actor_tenant_id,
            actor_customer_id=actor_customer_id,
            privileged=privileged,
        )
        row = self._artifacts.get_artifact(indexed.tenant_id, indexed.artifact_id)
        if row is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        now = self._clock.now()
        assert_can_delete(
            status=row.status,
            legal_hold=row.legal_hold,
            now=now,
            until=row.retention_until,
        )
        stored = self._artifacts.put_artifact(
            indexed.tenant_id,
            replace(
                row,
                status=ArtifactStatus.DELETED,
                deleted_at=now,
            ),
        )
        updated = self._index.save(self._to_index(stored))
        log_event(
            logger,
            "recording.deleted",
            outcome="success",
            tenant_id=str(updated.tenant_id),
            artifact_id=str(updated.artifact_id),
        )
        return self._payload(updated)

    def list_for_call(
        self,
        *,
        call_id: uuid.UUID,
        actor_tenant_id: uuid.UUID | None,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> list[dict[str, object]]:
        call = self._calls.get(call_id)
        if call is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        self._authorize_scope(
            tenant_id=call.tenant_id,
            customer_id=call.customer_id,
            actor_tenant_id=actor_tenant_id,
            actor_customer_id=actor_customer_id,
            privileged=privileged,
        )
        rows = self._artifacts.list_artifacts(call.tenant_id, call_id=call.call_id)
        if actor_customer_id is not None:
            rows = [row for row in rows if row.customer_id == actor_customer_id]
        return [self._payload(self._to_index(row)) for row in rows]

    def reconcile(self) -> dict[str, object]:
        orphan_objects: list[str] = []
        orphan_metadata: list[str] = []
        try:
            keys = set(self._store.list_keys())
        except RecordingStoreUnavailable:
            keys = set()
        indexed = self._index.list_all()
        by_key = {row.object_key: row for row in indexed}
        for key in keys:
            if key not in by_key:
                orphan_objects.append(key)
        for row in indexed:
            if row.status is ArtifactStatus.DELETED:
                continue
            try:
                present = self._store.exists(row.object_key)
            except RecordingStoreUnavailable:
                continue
            if not present:
                orphan_metadata.append(str(row.artifact_id))
        log_event(
            logger,
            "recording.reconcile",
            outcome="success",
            orphan_objects=len(orphan_objects),
            orphan_metadata=len(orphan_metadata),
        )
        return {
            "orphan_objects": orphan_objects,
            "orphan_metadata": orphan_metadata,
        }

    def _link_voicemail(self, call, object_ref: str) -> None:
        rows = self._media.list_voicemail(call.tenant_id, call_id=call.call_id)
        now = self._clock.now()
        for row in rows:
            if row.object_ref:
                continue
            self._media.put_voicemail(
                call.tenant_id,
                replace(row, object_ref=object_ref, updated_at=now),
            )

    def _verify(self, indexed: ArtifactIndexRecord) -> ArtifactIndexRecord:
        row = self._artifacts.get_artifact(indexed.tenant_id, indexed.artifact_id)
        if row is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        try:
            stored = self._store.get(indexed.object_key)
        except RecordingStoreUnavailable:
            log_event(
                logger,
                "recording.verify.store_down",
                outcome="retry",
                artifact_id=str(indexed.artifact_id),
            )
            return indexed
        if stored is None:
            updated = self._artifacts.put_artifact(
                indexed.tenant_id, replace(row, status=ArtifactStatus.VERIFYING)
            )
            return self._index.save(self._to_index(updated))
        checksum = getattr(stored, "checksum", "")
        if checksum != row.checksum:
            updated = self._artifacts.put_artifact(
                indexed.tenant_id, replace(row, status=ArtifactStatus.FAILED)
            )
            return self._index.save(self._to_index(updated))
        updated = self._artifacts.put_artifact(
            indexed.tenant_id,
            replace(
                row,
                status=ArtifactStatus.READY,
                available_at=self._clock.now(),
            ),
        )
        return self._index.save(self._to_index(updated))

    def _resolve_call(self, command: IngestCommand):
        edge = (command.edge_call_id or "").strip()
        if edge:
            call = self._calls.get_by_edge(edge)
            if call is not None:
                return call
        parsed = self._parse_optional_id(command.call_id)
        if parsed is not None:
            call = self._calls.get(parsed)
            if call is not None:
                return call
        raise DomainError("not_found", "Resource not found.", http_status=404)

    def _authorized_artifact(
        self,
        *,
        call_id: uuid.UUID,
        artifact_id: uuid.UUID,
        actor_tenant_id: uuid.UUID | None,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> ArtifactIndexRecord:
        call = self._calls.get(call_id)
        indexed = self._index.get(artifact_id)
        if call is None or indexed is None or indexed.call_id != call.call_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        self._authorize_scope(
            tenant_id=call.tenant_id,
            customer_id=call.customer_id,
            actor_tenant_id=actor_tenant_id,
            actor_customer_id=actor_customer_id,
            privileged=privileged,
        )
        return indexed

    def _authorize_scope(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        actor_tenant_id: uuid.UUID | None,
        actor_customer_id: uuid.UUID | None,
        privileged: bool,
    ) -> None:
        if privileged:
            return
        if actor_tenant_id is None or actor_tenant_id != tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if actor_customer_id is not None and actor_customer_id != customer_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)

    def _require_index(self, artifact_id: uuid.UUID) -> ArtifactIndexRecord:
        indexed = self._index.get(artifact_id)
        if indexed is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        return indexed

    def _parse_optional_id(self, raw: str) -> uuid.UUID | None:
        value = (raw or "").strip()
        if not value:
            return None
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError, AttributeError):
            return None

    def _to_index(self, row: TenantArtifactRecord) -> ArtifactIndexRecord:
        return ArtifactIndexRecord(
            artifact_id=row.artifact_id,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            call_id=row.call_id,
            kind=row.kind,
            object_key=row.object_key,
            checksum=row.checksum,
            status=row.status,
            legal_hold=row.legal_hold,
        )

    def _payload(self, row: ArtifactIndexRecord) -> dict[str, object]:
        return {
            "id": str(row.artifact_id),
            "call_id": str(row.call_id),
            "agency_id": str(row.tenant_id),
            "customer_id": str(row.customer_id),
            "kind": row.kind.value,
            "object_key": row.object_key,
            "status": row.status.value,
            "legal_hold": row.legal_hold,
            "checksum": row.checksum,
        }
