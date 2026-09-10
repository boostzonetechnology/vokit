from __future__ import annotations

from django.apps import AppConfig


class AgentsConfig(AppConfig):
    name = "control_plane.agents"
    label = "agents"
    verbose_name = "Agents"
