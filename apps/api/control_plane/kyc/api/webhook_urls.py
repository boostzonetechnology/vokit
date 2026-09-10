from __future__ import annotations

from django.urls import path

from control_plane.kyc.api.views import KycWebhookView

urlpatterns = [
    path(
        "kyc/<str:provider>/v1/",
        KycWebhookView.as_view(),
        name="kyc-webhook",
    ),
]
