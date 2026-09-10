from __future__ import annotations

from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.notifications.application.service import NotificationControl
from control_plane.notifications.infrastructure.mailer import DjangoMailer
from control_plane.notifications.infrastructure.repositories import (
    DjangoDeliveryRepository,
    DjangoInboxRepository,
    DjangoPreferenceRepository,
    DjangoTemplateRepository,
)


def notifications() -> NotificationControl:
    return NotificationControl(
        DjangoTemplateRepository(),
        DjangoInboxRepository(),
        DjangoDeliveryRepository(),
        DjangoPreferenceRepository(),
        DjangoMailer(),
        SystemClock(),
    )
