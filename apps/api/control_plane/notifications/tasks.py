from __future__ import annotations

import logging
import uuid

from config.celery import app
from control_plane.notifications.domain.types import DeliveryStatus
from control_plane.notifications.infrastructure.mailer import DjangoMailer
from control_plane.notifications.infrastructure.repositories import (
    DjangoDeliveryRepository,
)
from shared_kernel.http.correlation import set_correlation_id
from shared_kernel.logging import log_event

logger = logging.getLogger("vokit.notifications")

_RETRYABLE = (OSError, TimeoutError, ConnectionError)


@app.task(
    name="notifications.send_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
)
def send_email_task(
    self,
    delivery_id: str,
    to: str,
    subject: str,
    body: str,
    correlation_id: str = "",
    html_body: str = "",
) -> None:
    """Send a rendered email and update the delivery row. Do not log body/token."""
    if correlation_id:
        set_correlation_id(correlation_id)
    deliveries = DjangoDeliveryRepository()
    identifier = uuid.UUID(delivery_id)
    existing = deliveries.get(identifier)
    if existing is None:
        log_event(
            logger,
            "notification.email.missing_delivery",
            severity="warning",
            outcome="failure",
            delivery_id=delivery_id,
        )
        return
    if existing.status is DeliveryStatus.SENT:
        return
    try:
        DjangoMailer().send(to=to, subject=subject, body=body, html_body=html_body)
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, _RETRYABLE) and self.request.retries < self.max_retries:
            raise self.retry(exc=exc) from exc
        deliveries.update_status(
            identifier,
            status=DeliveryStatus.FAILED,
            error=str(exc)[:255],
        )
        log_event(
            logger,
            "notification.email.failed",
            severity="warning",
            outcome="failure",
            delivery_id=delivery_id,
            event_type=existing.event_type,
        )
        return
    deliveries.update_status(identifier, status=DeliveryStatus.SENT, error="")
    log_event(
        logger,
        "notification.email.sent",
        outcome="success",
        delivery_id=delivery_id,
        event_type=existing.event_type,
    )
