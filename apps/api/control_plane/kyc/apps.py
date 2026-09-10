from __future__ import annotations

from django.apps import AppConfig


class KycConfig(AppConfig):
    name = "control_plane.kyc"
    label = "kyc"
    verbose_name = "Agency KYC"
