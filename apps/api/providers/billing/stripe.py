from __future__ import annotations

from control_plane.billing.application.ports import NormalizedPaymentEvent
from providers.billing.normalize import parse_payment_event
from shared_kernel.hmac import verify_hmac_sha256


class StripePaymentAdapter:
    slug = "stripe"

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
