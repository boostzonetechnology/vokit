"""MFA TOTP vault — Family B secrets (ADR-008)."""

from __future__ import annotations

import pytest

from control_plane.identity.infrastructure.mfa_vault import MfaSecretVault
from shared_kernel.errors import DomainError


@pytest.mark.django_db
def test_mfa_vault_round_trip() -> None:
    vault = MfaSecretVault()
    ciphertext = vault.encrypt("JBSWY3DPEHPK3PXP")
    assert ciphertext
    assert "JBSWY3DPEHPK3PXP" not in ciphertext
    assert vault.decrypt(ciphertext) == "JBSWY3DPEHPK3PXP"


@pytest.mark.django_db
def test_mfa_vault_rejects_empty_and_bad_signature() -> None:
    vault = MfaSecretVault()
    with pytest.raises(DomainError) as empty:
        vault.encrypt("")
    assert empty.value.code == "secret_missing"
    with pytest.raises(DomainError) as bad:
        vault.decrypt("not-a-valid-signature")
    assert bad.value.code == "secret_missing"
