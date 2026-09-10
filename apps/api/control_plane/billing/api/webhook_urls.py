from __future__ import annotations

from django.urls import path

from control_plane.billing.api.views import PaymentWebhookView

urlpatterns = [
    path(
        "stripe/v1/",
        PaymentWebhookView.as_view(),
        {"processor": "stripe"},
        name="billing-stripe-webhook",
    ),
    path(
        "braintree/v1/",
        PaymentWebhookView.as_view(),
        {"processor": "braintree"},
        name="billing-braintree-webhook",
    ),
]
