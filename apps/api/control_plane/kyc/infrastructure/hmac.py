from __future__ import annotations

from shared_kernel.hmac import sign_hmac_sha256, verify_hmac_sha256


def verify_kyc_signature(*, secret_ref: str, raw_body: bytes, header: str) -> None:
    verify_hmac_sha256(
        secret_ref=secret_ref,
        raw_body=raw_body,
        header=header,
        error_code="kyc_signature_invalid",
        message="Webhook signature is invalid.",
    )


def sign_kyc_body(*, secret_ref: str, raw_body: bytes) -> str:
    return sign_hmac_sha256(secret_ref=secret_ref, raw_body=raw_body)
