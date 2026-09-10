"""HMAC helpers for inbound webhooks. Never log the resolved secret."""

from __future__ import annotations

import hmac
from hashlib import sha256

from shared_kernel.errors import DomainError
from shared_kernel.secrets import SecretRef


def sign_hmac_raw(*, secret: str, raw_body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), raw_body, sha256).hexdigest()
    return f"sha256={digest}"


def sign_hmac_sha256(*, secret_ref: str, raw_body: bytes) -> str:
    secret = SecretRef(secret_ref).resolve()
    return sign_hmac_raw(secret=secret, raw_body=raw_body)


def verify_hmac_sha256(
    *,
    secret_ref: str,
    raw_body: bytes,
    header: str,
    error_code: str,
    message: str,
) -> None:
    secret = SecretRef(secret_ref).resolve()
    provided = (header or "").strip()
    if provided.lower().startswith("sha256="):
        provided = provided[7:]
    expected = hmac.new(secret.encode("utf-8"), raw_body, sha256).hexdigest()
    if not provided or not hmac.compare_digest(provided, expected):
        raise DomainError(error_code, message, http_status=401)
