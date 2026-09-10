from __future__ import annotations

from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    name = "control_plane.integrations"
    label = "integrations"
    verbose_name = "Integrations"
