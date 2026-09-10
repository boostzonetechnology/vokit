from __future__ import annotations

from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = "control_plane.audit"
    label = "audit"
    verbose_name = "Audit"
