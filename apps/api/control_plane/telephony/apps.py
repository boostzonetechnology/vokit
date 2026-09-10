from __future__ import annotations

from django.apps import AppConfig


class TelephonyConfig(AppConfig):
    name = "control_plane.telephony"
    label = "telephony"
    verbose_name = "Telephony numbers"
