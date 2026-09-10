from __future__ import annotations

import pytest

from shared_kernel.errors import DomainError
from shared_kernel.phone import normalize_e164


def test_normalizes_e164() -> None:
    assert normalize_e164(" +1 (800) 555-1212 ") == "+18005551212"


def test_rejects_national_format() -> None:
    with pytest.raises(DomainError) as exc:
        normalize_e164("8005551212")
    assert exc.value.code == "invalid_phone"
