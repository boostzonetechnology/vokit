from __future__ import annotations

from django.apps import AppConfig


class TenancyConfig(AppConfig):
    name = "control_plane.tenancy"
    label = "tenancy"
    verbose_name = "Tenant Registry"
