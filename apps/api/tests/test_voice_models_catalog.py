from __future__ import annotations

from unittest.mock import patch

import pytest

from providers.voice.models_catalog import list_provider_models
from shared_kernel.errors import DomainError


def test_openai_llm_models_normalize() -> None:
    with patch(
        "providers.voice.models_catalog.vendor_get",
        return_value={"data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]},
    ):
        payload = list_provider_models("openai", "llm", "sk-test")
    assert payload["provider"] == "openai"
    assert payload["capability"] == "llm"
    assert [row["id"] for row in payload["models"]] == ["gpt-4o", "gpt-4o-mini"]


def test_missing_key_fails_closed() -> None:
    with pytest.raises(DomainError) as exc:
        list_provider_models("openai", "llm", "  ")
    assert exc.value.code == "secret_missing"


def test_invalid_capability() -> None:
    with pytest.raises(DomainError) as exc:
        list_provider_models("openai", "embedding", "sk-test")
    assert exc.value.code == "validation_error"
