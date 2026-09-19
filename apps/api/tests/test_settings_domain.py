from __future__ import annotations

from datetime import UTC, datetime

import pytest

from control_plane.commission.domain.policies import hold_available_at
from control_plane.platform_settings.domain.policies import (
    assert_setting_key,
    coerce_value,
    public_value,
)
from shared_kernel.errors import DomainError


def test_hold_days_are_bounded_and_used() -> None:
    spec = assert_setting_key("payout.hold_days")
    assert coerce_value(spec, 21) == 21
    with pytest.raises(DomainError):
        coerce_value(spec, 400)
    earned = datetime(2026, 9, 1, tzinfo=UTC)
    assert hold_available_at(earned, 21) == datetime(2026, 9, 22, tzinfo=UTC)
    proof = assert_setting_key("payout.proof_required")
    assert coerce_value(proof, True) is True
    assert coerce_value(proof, False) is False
    issuer = assert_setting_key("payout.receipt_issuer")
    assert coerce_value(issuer, "Vokit Finance") == "Vokit Finance"


def test_secret_settings_are_not_returned() -> None:
    spec = assert_setting_key("telephony.stt_api_key_ref")
    assert public_value(spec, "VOICE_STT_API_KEY") is None
    voice_key = assert_setting_key("voice.deepgram.api_key")
    assert public_value(voice_key, "dg-secret") is None


def test_voice_provider_codes_are_allowlisted() -> None:
    spec = assert_setting_key("telephony.llm_provider")
    assert coerce_value(spec, "anthropic") == "anthropic"
    assert coerce_value(spec, "") == ""
    with pytest.raises(DomainError) as exc:
        coerce_value(spec, "foo")
    assert exc.value.code == "validation_error"
    stt = assert_setting_key("telephony.stt_provider")
    with pytest.raises(DomainError):
        coerce_value(stt, "openai")


def test_voice_api_keys_allow_long_strings() -> None:
    spec = assert_setting_key("voice.openai.api_key")
    long_key = "sk-" + ("a" * 200)
    assert coerce_value(spec, long_key) == long_key
