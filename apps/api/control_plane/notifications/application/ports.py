from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.notifications.domain.types import (
    DeliveryStatus,
    NotificationCategory,
    NotificationChannel,
    PreferenceScope,
)


@dataclass(frozen=True, slots=True)
class TemplateRecord:
    id: uuid.UUID
    event_type: str
    channel: NotificationChannel
    subject: str
    body: str
    version: int


@dataclass(frozen=True, slots=True)
class InAppRecord:
    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    event_type: str
    category: NotificationCategory
    title: str
    body: str
    read_at: datetime | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class DeliveryRecord:
    id: uuid.UUID
    user_id: uuid.UUID | None
    recipient_email: str
    channel: NotificationChannel
    event_type: str
    status: DeliveryStatus
    error: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PreferenceRecord:
    id: uuid.UUID
    scope: PreferenceScope
    user_id: uuid.UUID | None
    tenant_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    event_type: str
    email_enabled: bool
    in_app_enabled: bool


@dataclass(frozen=True, slots=True)
class Recipient:
    user_id: uuid.UUID | None
    email: str
    tenant_id: uuid.UUID | None
    customer_id: uuid.UUID | None


class TemplateRepository(Protocol):
    def list_all(self) -> list[TemplateRecord]: ...
    def get(self, event_type: str, channel: NotificationChannel) -> TemplateRecord | None: ...
    def upsert(self, record: TemplateRecord) -> TemplateRecord: ...


class InboxRepository(Protocol):
    def create(self, record: InAppRecord) -> None: ...
    def list_for_user(self, user_id: uuid.UUID) -> list[InAppRecord]: ...
    def get_for_user(
        self, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> InAppRecord | None: ...
    def mark_read(
        self, notification_id: uuid.UUID, user_id: uuid.UUID, read_at: datetime
    ) -> None: ...


class DeliveryRepository(Protocol):
    def create(self, record: DeliveryRecord) -> None: ...
    def get(self, delivery_id: uuid.UUID) -> DeliveryRecord | None: ...
    def update_status(
        self,
        delivery_id: uuid.UUID,
        *,
        status: DeliveryStatus,
        error: str = "",
    ) -> None: ...
    def list_all(self) -> list[DeliveryRecord]: ...


class PreferenceRepository(Protocol):
    def list_for_scope(
        self,
        *,
        scope: PreferenceScope,
        user_id: uuid.UUID | None,
        tenant_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
    ) -> list[PreferenceRecord]: ...
    def upsert(self, record: PreferenceRecord) -> PreferenceRecord: ...


class Mailer(Protocol):
    def send(self, *, to: str, subject: str, body: str) -> None: ...
