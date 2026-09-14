"""Encrypt voice vendor API keys at rest (Family B; ADR-008 §4b).

Distinct salt from MFA (`identity_mfa_totp`) and tenant DB (`tenant_db_pwd`).
"""

from __future__ import annotations

from django.conf import settings
from django.core import signing

from shared_kernel.errors import DomainError

_VAULT_SALT = "voice_provider_api_key"


class VoiceProviderVault:
    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            raise DomainError("validation_error", "API key is required.")
        return signing.dumps(plaintext, salt=_VAULT_SALT, key=settings.SECRET_KEY)

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            value = signing.loads(ciphertext, salt=_VAULT_SALT, key=settings.SECRET_KEY)
        except signing.BadSignature as exc:
            raise DomainError(
                "secret_missing",
                "Required secret is not configured.",
                http_status=503,
            ) from exc
        if not isinstance(value, str):
            return ""
        return value.strip()
