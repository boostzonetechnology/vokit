from __future__ import annotations

from django.apps import AppConfig


class RiskConfig(AppConfig):
    name = "control_plane.risk"
    label = "risk"
    verbose_name = "Customer Risk"
