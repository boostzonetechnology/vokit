from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from control_plane.notifications.application.ports import DeliveryRecord
from control_plane.notifications.domain.types import (
    DeliveryStatus,
    NotificationChannel,
)
from control_plane.notifications.infrastructure.repositories import (
    DjangoDeliveryRepository,
)
from control_plane.notifications.tasks import send_email_task
from shared_kernel.ids import new_uuid7


@pytest.mark.django_db
def test_send_email_task_marks_delivery_sent() -> None:
    delivery_id = new_uuid7()
    DjangoDeliveryRepository().create(
        DeliveryRecord(
            id=delivery_id,
            user_id=None,
            recipient_email="queue@vokit.test",
            channel=NotificationChannel.EMAIL,
            event_type="invitation.customer",
            status=DeliveryStatus.QUEUED,
            error="",
            created_at=timezone.now(),
        )
    )
    mail.outbox.clear()
    send_email_task.run(
        str(delivery_id),
        "queue@vokit.test",
        "Subject",
        "Body with secret-token-xyz",
        "",
    )
    assert len(mail.outbox) == 1
    assert "secret-token-xyz" in mail.outbox[0].body
    row = DjangoDeliveryRepository().get(delivery_id)
    assert row is not None
    assert row.status is DeliveryStatus.SENT
    assert row.error == ""


@pytest.mark.django_db
def test_send_email_task_marks_failed_without_raising_permanent() -> None:
    delivery_id = new_uuid7()
    DjangoDeliveryRepository().create(
        DeliveryRecord(
            id=delivery_id,
            user_id=None,
            recipient_email="fail@vokit.test",
            channel=NotificationChannel.EMAIL,
            event_type="invitation.customer",
            status=DeliveryStatus.QUEUED,
            error="",
            created_at=timezone.now(),
        )
    )
    with patch(
        "control_plane.notifications.tasks.DjangoMailer.send",
        side_effect=RuntimeError("smtp down"),
    ):
        send_email_task.run(
            str(delivery_id),
            "fail@vokit.test",
            "Subject",
            "Body",
            "",
        )
    row = DjangoDeliveryRepository().get(delivery_id)
    assert row is not None
    assert row.status is DeliveryStatus.FAILED
    assert "smtp down" in row.error
