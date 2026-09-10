from __future__ import annotations

from django.conf import settings

from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.recordings.application.service import RecordingControl
from control_plane.recordings.infrastructure.repositories import (
    DjangoAccessGrantRepository,
    DjangoArtifactIndexRepository,
    DjangoIngestEventRepository,
)
from control_plane.telephony.infrastructure.container import tenant_media
from control_plane.telephony.infrastructure.repositories import DjangoCallIndexRepository
from control_plane.tenancy.infrastructure.container import router, runtime
from providers.recordings.memory import MemoryRecordingStore
from tenant.recordings.service import TenantRecordingService

_store: MemoryRecordingStore | None = None


def reset_recording_store() -> None:
    global _store
    if _store is not None:
        _store.reset()
    _store = None


def recording_store() -> MemoryRecordingStore:
    global _store
    if _store is None:
        _store = MemoryRecordingStore()
    return _store


def tenant_recordings() -> TenantRecordingService:
    return TenantRecordingService(router(), runtime())


def recording_control() -> RecordingControl:
    return RecordingControl(
        DjangoCallIndexRepository(),
        tenant_recordings(),
        tenant_media(),
        DjangoArtifactIndexRepository(),
        DjangoIngestEventRepository(),
        DjangoAccessGrantRepository(),
        recording_store(),
        SystemClock(),
        retention_days=int(getattr(settings, "RECORDING_DEFAULT_RETENTION_DAYS", 30)),
        access_ttl_seconds=int(getattr(settings, "RECORDING_ACCESS_TTL_SECONDS", 60)),
        public_base_url=str(
            getattr(settings, "RECORDING_PUBLIC_BASE_URL", "https://recordings.vokit.test")
        ),
    )
