from __future__ import annotations

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "control_plane.notifications"
    label = "notifications"
    verbose_name = "Notifications"
