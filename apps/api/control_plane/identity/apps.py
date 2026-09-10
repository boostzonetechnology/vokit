from __future__ import annotations

from django.apps import AppConfig


class IdentityConfig(AppConfig):
    name = "control_plane.identity"
    label = "identity"
    verbose_name = "Identity & Access"
