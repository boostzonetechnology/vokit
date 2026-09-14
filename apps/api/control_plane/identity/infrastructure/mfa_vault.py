"""Encrypt MFA TOTP secrets at rest (app-vault Family B; ADR-008).

Same Django signing pattern as tenant DB vault (`tenant_db_pwd`), distinct salt.
Not a SecretRef — per-user ciphertext lives on `identity_mfa_methods`.
"""

from __future__ import annotations

from django.conf import settings
from django.core import signing

from shared_kernel.errors import DomainError

_VAULT_SALT = "identity_mfa_totp"


class MfaSecretVault:
    """Family B vault: ciphertext in DB; master = SECRET_KEY until KMS envelope."""

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            raise DomainError("secret_missing", "MFA secret is missing.", http_status=503)
        return signing.dumps(plaintext, salt=_VAULT_SALT, key=settings.SECRET_KEY)[:1024]

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            raise DomainError("secret_missing", "MFA secret is missing.", http_status=503)
        try:
            value = signing.loads(ciphertext, salt=_VAULT_SALT, key=settings.SECRET_KEY)
        except signing.BadSignature as exc:
            raise DomainError(
                "secret_missing",
                "MFA secret is missing.",
                http_status=503,
            ) from exc
        if not isinstance(value, str) or not value:
            raise DomainError("secret_missing", "MFA secret is missing.", http_status=503)
        return value
