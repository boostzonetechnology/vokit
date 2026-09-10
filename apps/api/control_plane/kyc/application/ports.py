from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.kyc.domain.types import KycStatus, ProviderEventStatus


@dataclass(frozen=True, slots=True)
class KycCaseRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    status: KycStatus
    provider_slug: str
    session_id: str
    inquiry_id: str
    last_event_id: str
    reason_code: str
    external_note: str
    internal_note: str
    frozen: bool
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class KycSettingsRecord:
    provider_slug: str
    api_key_ref: str
    webhook_secret_ref: str
    hosted_base_url: str


@dataclass(frozen=True, slots=True)
class ProviderSession:
    session_id: str
    inquiry_id: str
    hosted_url: str


@dataclass(frozen=True, slots=True)
class MappedProviderEvent:
    event_id: str
    session_id: str
    inquiry_id: str
    status: KycStatus
    reason_code: str
    external_note: str


class KycCaseRepository(Protocol):
    def get(self, case_id: uuid.UUID) -> KycCaseRecord | None: ...

    def get_for_tenant(self, tenant_id: uuid.UUID) -> KycCaseRecord | None: ...

    def get_by_session(self, session_id: str) -> KycCaseRecord | None: ...

    def list(self, *, status: KycStatus | None = None) -> list[KycCaseRecord]: ...

    def create(self, record: KycCaseRecord) -> None: ...

    def update(self, record: KycCaseRecord) -> None: ...


class KycSettingsRepository(Protocol):
    def get(self) -> KycSettingsRecord: ...

    def save(self, record: KycSettingsRecord) -> None: ...


class KycEventRepository(Protocol):
    def get_by_event_id(self, event_id: str) -> ProviderEventStatus | None: ...

    def record(
        self,
        *,
        event_id: str,
        case_id: uuid.UUID | None,
        mapped_status: KycStatus | None,
        reason_code: str,
        status: ProviderEventStatus,
    ) -> None: ...


class KycProvider(Protocol):
    slug: str

    def start_or_resume(
        self, settings: KycSettingsRecord, case: KycCaseRecord | None
    ) -> ProviderSession: ...
