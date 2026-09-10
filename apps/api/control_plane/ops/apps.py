from __future__ import annotations

from django.apps import AppConfig


class OpsConfig(AppConfig):
    name = "control_plane.ops"
    label = "ops"
    verbose_name = "Production operations"
