from __future__ import annotations

from django.apps import AppConfig


class CustomersConfig(AppConfig):
    name = "control_plane.customers"
    label = "customers"
    verbose_name = "Customer Index"
