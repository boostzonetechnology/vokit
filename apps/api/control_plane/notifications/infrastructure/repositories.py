from __future__ import annotations

import uuid
from datetime import datetime

from control_plane.notifications.application.ports import (
    DeliveryRecord,
    InAppRecord,
    PreferenceRecord,
    TemplateRecord,
)
from control_plane.notifications.domain.types import (
    DeliveryStatus,
    NotificationCategory,
    NotificationChannel,
    PreferenceScope,
)
from control_plane.notifications.models import (
    InAppNotification,
    NotificationDelivery,
    NotificationPreference,
    NotificationTemplate,
)


def _template(row: NotificationTemplate) -> TemplateRecord:
    return TemplateRecord(
        id=row.id,
        event_type=row.event_type,
        channel=NotificationChannel(row.channel),
        subject=row.subject,
        body=row.body,
        version=row.version,
    )


def _inbox(row: InAppNotification) -> InAppRecord:
    return InAppRecord(
        id=row.id,
        user_id=row.user_id,
        tenant_id=row.tenant_id,
        customer_id=row.customer_id,
        event_type=row.event_type,
        category=NotificationCategory(row.category),
        title=row.title,
        body=row.body,
        read_at=row.read_at,
        created_at=row.created_at,
    )


class DjangoTemplateRepository:
    def list_all(self) -> list[TemplateRecord]:
        return [_template(row) for row in NotificationTemplate.objects.order_by("event_type")]

    def get(self, event_type: str, channel: NotificationChannel) -> TemplateRecord | None:
        row = NotificationTemplate.objects.filter(
            event_type=event_type, channel=channel.value
        ).first()
        return _template(row) if row else None

    def upsert(self, record: TemplateRecord) -> TemplateRecord:
        existing = NotificationTemplate.objects.filter(
            event_type=record.event_type, channel=record.channel.value
        ).first()
        if existing is None:
            NotificationTemplate.objects.create(
                id=record.id,
                event_type=record.event_type,
                channel=record.channel.value,
                subject=record.subject,
                body=record.body,
                version=record.version,
            )
        else:
            existing.subject = record.subject
            existing.body = record.body
            existing.version = record.version
            existing.save(update_fields=["subject", "body", "version", "updated_at"])
        stored = self.get(record.event_type, record.channel)
        return stored or record


class DjangoInboxRepository:
    def create(self, record: InAppRecord) -> None:
        InAppNotification.objects.create(
            id=record.id,
            user_id=record.user_id,
            tenant_id=record.tenant_id,
            customer_id=record.customer_id,
            event_type=record.event_type,
            category=record.category.value,
            title=record.title,
            body=record.body,
            read_at=record.read_at,
            created_at=record.created_at,
        )

    def list_for_user(self, user_id: uuid.UUID) -> list[InAppRecord]:
        rows = InAppNotification.objects.filter(user_id=user_id).order_by("-created_at")
        return [_inbox(row) for row in rows]

    def get_for_user(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> InAppRecord | None:
        row = InAppNotification.objects.filter(id=notification_id, user_id=user_id).first()
        return _inbox(row) if row else None

    def mark_read(
        self, notification_id: uuid.UUID, user_id: uuid.UUID, read_at: datetime
    ) -> None:
        InAppNotification.objects.filter(id=notification_id, user_id=user_id).update(
            read_at=read_at
        )


class DjangoDeliveryRepository:
    def create(self, record: DeliveryRecord) -> None:
        NotificationDelivery.objects.create(
            id=record.id,
            user_id=record.user_id,
            recipient_email=record.recipient_email,
            channel=record.channel.value,
            event_type=record.event_type,
            status=record.status.value,
            error=record.error,
            created_at=record.created_at,
        )

    def get(self, delivery_id: uuid.UUID) -> DeliveryRecord | None:
        row = NotificationDelivery.objects.filter(id=delivery_id).first()
        if row is None:
            return None
        return DeliveryRecord(
            id=row.id,
            user_id=row.user_id,
            recipient_email=row.recipient_email,
            channel=NotificationChannel(row.channel),
            event_type=row.event_type,
            status=DeliveryStatus(row.status),
            error=row.error,
            created_at=row.created_at,
        )

    def update_status(
        self,
        delivery_id: uuid.UUID,
        *,
        status: DeliveryStatus,
        error: str = "",
    ) -> None:
        NotificationDelivery.objects.filter(id=delivery_id).update(
            status=status.value,
            error=error[:255],
        )

    def list_all(self) -> list[DeliveryRecord]:
        rows = NotificationDelivery.objects.order_by("-created_at")
        return [
            DeliveryRecord(
                id=row.id,
                user_id=row.user_id,
                recipient_email=row.recipient_email,
                channel=NotificationChannel(row.channel),
                event_type=row.event_type,
                status=DeliveryStatus(row.status),
                error=row.error,
                created_at=row.created_at,
            )
            for row in rows
        ]


class DjangoPreferenceRepository:
    def list_for_scope(
        self,
        *,
        scope: PreferenceScope,
        user_id: uuid.UUID | None,
        tenant_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
    ) -> list[PreferenceRecord]:
        query = NotificationPreference.objects.filter(scope=scope.value)
        if scope is PreferenceScope.USER:
            query = query.filter(user_id=user_id)
        elif scope is PreferenceScope.AGENCY:
            query = query.filter(tenant_id=tenant_id, customer_id__isnull=True)
        else:
            query = query.filter(tenant_id=tenant_id, customer_id=customer_id)
        return [
            PreferenceRecord(
                id=row.id,
                scope=PreferenceScope(row.scope),
                user_id=row.user_id,
                tenant_id=row.tenant_id,
                customer_id=row.customer_id,
                event_type=row.event_type,
                email_enabled=row.email_enabled,
                in_app_enabled=row.in_app_enabled,
            )
            for row in query
        ]

    def upsert(self, record: PreferenceRecord) -> PreferenceRecord:
        filters: dict = {
            "scope": record.scope.value,
            "event_type": record.event_type,
        }
        if record.scope is PreferenceScope.USER:
            filters["user_id"] = record.user_id
        elif record.scope is PreferenceScope.AGENCY:
            filters["tenant_id"] = record.tenant_id
            filters["customer_id"] = None
        else:
            filters["tenant_id"] = record.tenant_id
            filters["customer_id"] = record.customer_id
        NotificationPreference.objects.update_or_create(
            **filters,
            defaults={
                "user_id": record.user_id,
                "tenant_id": record.tenant_id,
                "customer_id": record.customer_id,
                "email_enabled": record.email_enabled,
                "in_app_enabled": record.in_app_enabled,
            },
        )
        rows = self.list_for_scope(
            scope=record.scope,
            user_id=record.user_id,
            tenant_id=record.tenant_id,
            customer_id=record.customer_id,
        )
        for row in rows:
            if row.event_type == record.event_type:
                return row
        return record
