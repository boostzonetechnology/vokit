from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings

from control_plane.billing.application.ports import NormalizedPaymentEvent
from providers.billing.normalize import parse_payment_event
from shared_kernel.hmac import verify_hmac_sha256


class SandboxPaymentAdapter:
    slug = "sandbox"

    def verify_and_normalize(
        self, *, raw_body: bytes, signature_header: str, secret_ref: str
    ) -> NormalizedPaymentEvent:
        verify_hmac_sha256(
            secret_ref=secret_ref,
            raw_body=raw_body,
            header=signature_header,
            error_code="payment_signature_invalid",
            message="Webhook signature is invalid.",
        )
        return parse_payment_event(self.slug, raw_body)


def sandbox_checkout_url(
    *,
    invoice_id: str,
    amount_minor: int,
    currency: str,
    client_reference: str,
) -> str | None:
    base = str(getattr(settings, "SANDBOX_PAYMENT_BASE_URL", "") or "").rstrip("/")
    if not base:
        return None
    query = urlencode(
        {
            "invoice_id": invoice_id,
            "amount_minor": str(amount_minor),
            "currency": currency,
            "client_reference": client_reference,
        }
    )
    return f"{base}/checkout?{query}"
