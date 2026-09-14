"""Voice vendor API keys — Family B vault (ADR-008 §4b)."""

from __future__ import annotations

import pytest

from control_plane.platform_settings.infrastructure.voice_vault import VoiceProviderVault
from shared_kernel.errors import DomainError


@pytest.mark.django_db
def test_voice_vault_round_trip() -> None:
    vault = VoiceProviderVault()
    ciphertext = vault.encrypt("sk-live-example-key")
    assert ciphertext
    assert "sk-live-example-key" not in ciphertext
    assert vault.decrypt(ciphertext) == "sk-live-example-key"


@pytest.mark.django_db
def test_voice_vault_rejects_empty_and_bad_signature() -> None:
    vault = VoiceProviderVault()
    with pytest.raises(DomainError) as empty:
        vault.encrypt("")
    assert empty.value.code == "validation_error"
    with pytest.raises(DomainError) as bad:
        vault.decrypt("not-a-valid-signature")
    assert bad.value.code == "secret_missing"
    assert vault.decrypt("") == ""
