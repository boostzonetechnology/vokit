from __future__ import annotations

import pytest

from shared_kernel.errors import DomainError
from shared_kernel.secrets import SecretRef


def test_resolve_and_never_stringify_value() -> None:
    ref = SecretRef("VOKIT_TEST_SECRET")
    value = ref.resolve({"VOKIT_TEST_SECRET": "super-secret"})
    assert value == "super-secret"
    assert "super-secret" not in str(ref)
    assert "super-secret" not in repr(ref)


def test_missing_secret_fails_closed() -> None:
    with pytest.raises(DomainError) as exc:
        SecretRef("MISSING_SECRET").resolve({})
    assert exc.value.code == "secret_missing"
    assert exc.value.http_status == 503


def test_rejects_whitespace_key() -> None:
    with pytest.raises(DomainError):
        SecretRef("NOT A KEY")
