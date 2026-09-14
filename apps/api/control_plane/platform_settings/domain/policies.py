from __future__ import annotations

from control_plane.platform_settings.domain.types import (
    FEATURE_FLAGS,
    SETTING_CATALOG,
    SettingSpec,
)
from control_plane.platform_settings.domain.voice_catalog import (
    assert_provider_code,
    is_voice_secret_key,
)
from shared_kernel.errors import DomainError


def assert_setting_key(raw: str) -> SettingSpec:
    spec = SETTING_CATALOG.get((raw or "").strip())
    if spec is None:
        raise DomainError("validation_error", "setting key is invalid.")
    return spec


def assert_flag(raw: str) -> str:
    name = (raw or "").strip()
    if name not in FEATURE_FLAGS:
        raise DomainError("validation_error", "flag is invalid.")
    return name


def coerce_value(spec: SettingSpec, raw: object) -> object:
    if spec.value_type == "int":
        if type(raw) is bool or type(raw) is float or raw is None:
            raise DomainError("validation_error", f"{spec.key} must be an integer.")
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise DomainError("validation_error", f"{spec.key} must be an integer.") from exc
        if spec.key == "payout.hold_days" and (value < 0 or value > 365):
            raise DomainError("validation_error", "hold_days must be between 0 and 365.")
        return value
    if spec.value_type == "bool":
        if type(raw) is not bool:
            raise DomainError("validation_error", f"{spec.key} must be a boolean.")
        return raw
    if type(raw) is not str:
        raise DomainError("validation_error", f"{spec.key} must be a string.")
    cleaned = raw.strip()
    if spec.key in {
        "telephony.stt_provider",
        "telephony.tts_provider",
        "telephony.llm_provider",
    }:
        return assert_provider_code(spec.key, cleaned)
    limit = 4096 if is_voice_secret_key(spec.key) else 128
    if len(cleaned) > limit:
        raise DomainError("validation_error", f"{spec.key} is too long.")
    return cleaned[:limit]


def public_value(spec: SettingSpec, stored: object) -> object | None:
    if spec.secret:
        return None
    return stored
