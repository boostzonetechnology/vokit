from __future__ import annotations

from django.apps import AppConfig


class BillingConfig(AppConfig):
    name = "control_plane.billing"
    label = "billing"
    verbose_name = "Billing"
