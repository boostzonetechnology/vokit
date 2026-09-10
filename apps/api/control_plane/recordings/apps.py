from __future__ import annotations

from django.apps import AppConfig


class RecordingsConfig(AppConfig):
    name = "control_plane.recordings"
    label = "recordings"
    verbose_name = "Recording metadata"
