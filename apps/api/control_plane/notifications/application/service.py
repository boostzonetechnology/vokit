from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.notifications.application.ports import (
    DeliveryRecord,
    DeliveryRepository,
    InAppRecord,
    InboxRepository,
    PreferenceRecord,
    PreferenceRepository,
    Recipient,
    TemplateRecord,
    TemplateRepository,
)
from control_plane.notifications.domain.policies import (
    assert_event_type,
    assert_preference_allowed,
    assert_template_body,
    category_for,
    is_mandatory,
    render_template,
)
from control_plane.notifications.domain.types import (
    DEFAULT_TEMPLATES,
    EMAIL_CTA,
    EMAIL_TITLES,
    EVENT_CATALOG,
    TEMPLATE_VARIABLES,
    DeliveryStatus,
    NotificationChannel,
    PreferenceScope,
)
from shared_kernel.errors import DomainError
from shared_kernel.http.correlation import get_correlation_id
from shared_kernel.ids import new_uuid7
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.notifications")

MAX_ANNOUNCEMENT_RECIPIENTS = 200


@dataclass(frozen=True, slots=True)
class DispatchCommand:
    event_type: str
    recipients: tuple[Recipient, ...]
    variables: dict[str, str]
    tenant_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None


class NotificationControl:
    def __init__(
        self,
        templates: TemplateRepository,
        inbox: InboxRepository,
        deliveries: DeliveryRepository,
        preferences: PreferenceRepository,
        clock: SystemClock,
    ) -> None:
        self._templates = templates
        self._inbox = inbox
        self._deliveries = deliveries
        self._preferences = preferences
        self._clock = clock

    def ensure_defaults(self) -> None:
        legacy_invite_marker = "Use this one-time token to accept"
        for event_type, bodies in DEFAULT_TEMPLATES.items():
            in_app = self._templates.get(event_type, NotificationChannel.IN_APP)
            if in_app is None:
                self._templates.upsert(
                    TemplateRecord(
                        id=new_uuid7(),
                        event_type=event_type,
                        channel=NotificationChannel.IN_APP,
                        subject=bodies["subject"],
                        body=bodies["body"],
                        version=1,
                    )
                )
            email = self._templates.get(event_type, NotificationChannel.EMAIL)
            if email is None:
                self._templates.upsert(
                    TemplateRecord(
                        id=new_uuid7(),
                        event_type=event_type,
                        channel=NotificationChannel.EMAIL,
                        subject=bodies["subject"],
                        body=bodies["email_body"],
                        version=1,
                    )
                )
            elif (
                event_type.startswith("invitation.")
                and legacy_invite_marker in (email.body or "")
            ):
                self._templates.upsert(
                    TemplateRecord(
                        id=email.id,
                        event_type=event_type,
                        channel=NotificationChannel.EMAIL,
                        subject=bodies["subject"],
                        body=bodies["email_body"],
                        version=email.version + 1,
                    )
                )

    def list_templates(self) -> list[dict[str, object]]:
        self.ensure_defaults()
        return [
            {
                "id": str(row.id),
                "event_type": row.event_type,
                "channel": row.channel.value,
                "subject": row.subject,
                "body": row.body,
                "version": row.version,
            }
            for row in self._templates.list_all()
        ]

    def update_template(
        self,
        *,
        event_type: str,
        channel: str,
        subject: str,
        body: str,
    ) -> dict[str, object]:
        name = assert_event_type(event_type)
        try:
            ch = NotificationChannel(channel.strip())
        except ValueError as exc:
            raise DomainError("validation_error", "channel is invalid.") from exc
        cleaned = assert_template_body(body, name)
        title = (subject or "").strip()
        if not title:
            raise DomainError("validation_error", "subject is required.")
        render_template(title, {key: "" for key in TEMPLATE_VARIABLES[name]}, name)
        existing = self._templates.get(name, ch)
        record = self._templates.upsert(
            TemplateRecord(
                id=existing.id if existing else new_uuid7(),
                event_type=name,
                channel=ch,
                subject=title[:255],
                body=cleaned,
                version=(existing.version + 1) if existing else 1,
            )
        )
        log_event(logger, "notification.template.updated", outcome="success", event_type=name)
        return {
            "id": str(record.id),
            "event_type": record.event_type,
            "channel": record.channel.value,
            "subject": record.subject,
            "body": record.body,
            "version": record.version,
        }

    def inbox_for(self, user_id: uuid.UUID) -> list[dict[str, object]]:
        return [self._inbox_payload(row) for row in self._inbox.list_for_user(user_id)]

    def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, object]:
        row = self._inbox.get_for_user(notification_id, user_id)
        if row is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if row.read_at is None:
            self._inbox.mark_read(notification_id, user_id, self._clock.now())
            row = self._inbox.get_for_user(notification_id, user_id) or row
        return self._inbox_payload(row)

    def list_preferences(
        self,
        *,
        scope: PreferenceScope,
        user_id: uuid.UUID | None,
        tenant_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
    ) -> list[dict[str, object]]:
        stored = {
            row.event_type: row
            for row in self._preferences.list_for_scope(
                scope=scope,
                user_id=user_id,
                tenant_id=tenant_id,
                customer_id=customer_id,
            )
        }
        items: list[dict[str, object]] = []
        for event_type in EVENT_CATALOG:
            row = stored.get(event_type)
            items.append(
                {
                    "event_type": event_type,
                    "category": EVENT_CATALOG[event_type].value,
                    "mandatory": is_mandatory(event_type),
                    "email": True if row is None else row.email_enabled,
                    "in_app": True if row is None else row.in_app_enabled,
                }
            )
        return items

    def set_preferences(
        self,
        *,
        scope: PreferenceScope,
        user_id: uuid.UUID | None,
        tenant_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
        items: list[dict],
    ) -> list[dict[str, object]]:
        for item in items:
            event_type = assert_event_type(str(item.get("event_type") or ""))
            email = bool(item.get("email", True))
            in_app = bool(item.get("in_app", True))
            assert_preference_allowed(event_type, email=email, in_app=in_app)
            self._preferences.upsert(
                PreferenceRecord(
                    id=new_uuid7(),
                    scope=scope,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    event_type=event_type,
                    email_enabled=email,
                    in_app_enabled=in_app,
                )
            )
        return self.list_preferences(
            scope=scope,
            user_id=user_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
        )

    def list_deliveries(self) -> list[dict[str, object]]:
        return [
            {
                "id": str(row.id),
                "user_id": str(row.user_id) if row.user_id else None,
                "recipient_email": row.recipient_email,
                "channel": row.channel.value,
                "event_type": row.event_type,
                "status": row.status.value,
                "error": row.error,
                "created_at": row.created_at.isoformat(),
            }
            for row in self._deliveries.list_all()
        ]

    def dispatch(self, command: DispatchCommand) -> int:
        self.ensure_defaults()
        event_type = assert_event_type(command.event_type)
        sent = 0
        for recipient in command.recipients[:MAX_ANNOUNCEMENT_RECIPIENTS]:
            email_on, in_app_on = self._channels_enabled(event_type, recipient)
            if in_app_on and recipient.user_id is not None:
                self._deliver_in_app(event_type, recipient, command.variables)
                sent += 1
            if email_on and recipient.email:
                self._deliver_email(event_type, recipient, command.variables)
                sent += 1
        log_event(
            logger,
            "notification.dispatched",
            outcome="success",
            event_type=event_type,
            recipients=len(command.recipients),
        )
        return sent

    def _channels_enabled(self, event_type: str, recipient: Recipient) -> tuple[bool, bool]:
        if is_mandatory(event_type):
            return True, True
        email_on = True
        in_app_on = True
        scopes = [
            self._preferences.list_for_scope(
                scope=PreferenceScope.USER,
                user_id=recipient.user_id,
                tenant_id=None,
                customer_id=None,
            )
        ]
        if recipient.tenant_id is not None and recipient.customer_id is None:
            scopes.append(
                self._preferences.list_for_scope(
                    scope=PreferenceScope.AGENCY,
                    user_id=None,
                    tenant_id=recipient.tenant_id,
                    customer_id=None,
                )
            )
        if recipient.customer_id is not None:
            scopes.append(
                self._preferences.list_for_scope(
                    scope=PreferenceScope.CUSTOMER,
                    user_id=None,
                    tenant_id=recipient.tenant_id,
                    customer_id=recipient.customer_id,
                )
            )
        for rows in scopes:
            for row in rows:
                if row.event_type != event_type:
                    continue
                email_on = email_on and row.email_enabled
                in_app_on = in_app_on and row.in_app_enabled
        return email_on, in_app_on

    def _deliver_in_app(
        self,
        event_type: str,
        recipient: Recipient,
        variables: dict[str, str],
    ) -> None:
        template = self._templates.get(event_type, NotificationChannel.IN_APP)
        if template is None or recipient.user_id is None:
            return
        safe_vars = {key: str(value) for key, value in variables.items() if key != "token"}
        title = render_template(template.subject, safe_vars, event_type)
        body = render_template(template.body, safe_vars, event_type)
        now = self._clock.now()
        record = InAppRecord(
            id=new_uuid7(),
            user_id=recipient.user_id,
            tenant_id=recipient.tenant_id,
            customer_id=recipient.customer_id,
            event_type=event_type,
            category=category_for(event_type),
            title=title[:255],
            body=body[:4000],
            read_at=None,
            created_at=now,
        )
        self._inbox.create(record)
        self._deliveries.create(
            DeliveryRecord(
                id=new_uuid7(),
                user_id=recipient.user_id,
                recipient_email=recipient.email,
                channel=NotificationChannel.IN_APP,
                event_type=event_type,
                status=DeliveryStatus.SENT,
                error="",
                created_at=now,
            )
        )

    def _deliver_email(
        self,
        event_type: str,
        recipient: Recipient,
        variables: dict[str, str],
    ) -> None:
        from django.conf import settings

        from control_plane.notifications.infrastructure.email_layout import (
            greeting_from_email,
            wrap_email_html,
        )
        from control_plane.notifications.tasks import send_email_task

        template = self._templates.get(event_type, NotificationChannel.EMAIL)
        now = self._clock.now()
        if template is None:
            self._deliveries.create(
                DeliveryRecord(
                    id=new_uuid7(),
                    user_id=recipient.user_id,
                    recipient_email=recipient.email,
                    channel=NotificationChannel.EMAIL,
                    event_type=event_type,
                    status=DeliveryStatus.FAILED,
                    error="template_missing",
                    created_at=now,
                )
            )
            return
        subject = render_template(template.subject, variables, event_type)
        body = render_template(template.body, variables, event_type)
        cta_url = ""
        cta_label = ""
        cta = EMAIL_CTA.get(event_type)
        if cta is not None:
            cta_label, url_key = cta
            cta_url = str(variables.get(url_key) or "")
        title = EMAIL_TITLES.get(event_type) or subject
        html_body = wrap_email_html(
            title=title,
            message=body,
            greeting=greeting_from_email(
                str(variables.get("email") or recipient.email or "")
            ),
            cta_url=cta_url,
            cta_label=cta_label,
        )
        if cta_url and cta_url not in body:
            body = f"{body}\n\n{cta_label or 'Open'}: {cta_url}"
        delivery_id = new_uuid7()
        self._deliveries.create(
            DeliveryRecord(
                id=delivery_id,
                user_id=recipient.user_id,
                recipient_email=recipient.email,
                channel=NotificationChannel.EMAIL,
                event_type=event_type,
                status=DeliveryStatus.QUEUED,
                error="",
                created_at=now,
            )
        )
        task_args = (
            str(delivery_id),
            recipient.email,
            subject,
            body,
            get_correlation_id() or "",
            html_body,
        )
        try:
            if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
                send_email_task.apply(args=task_args)
            else:
                send_email_task.delay(*task_args)
        except Exception as exc:  # noqa: BLE001
            self._deliveries.update_status(
                delivery_id,
                status=DeliveryStatus.FAILED,
                error=str(exc)[:255],
            )
            log_event(
                logger,
                "notification.email.enqueue_failed",
                severity="warning",
                outcome="failure",
                event_type=event_type,
                delivery_id=str(delivery_id),
            )

    def _inbox_payload(self, row: InAppRecord) -> dict[str, object]:
        return {
            "id": str(row.id),
            "event_type": row.event_type,
            "category": row.category.value,
            "title": row.title,
            "body": row.body,
            "read_at": row.read_at.isoformat() if row.read_at else None,
            "created_at": row.created_at.isoformat(),
        }
