from __future__ import annotations

from dataclasses import dataclass
from typing import Any

FEATURE_FLAGS = frozenset(
    {
        "recordings_live",
        "calling_live",
        "billing_live",
        "integrations",
        "outbound",
        "customer_edit",
        "templates",
    }
)


@dataclass(frozen=True, slots=True)
class SettingSpec:
    key: str
    default: Any
    secret: bool
    value_type: str


SETTING_CATALOG: dict[str, SettingSpec] = {
    "commercial.base_currency": SettingSpec("commercial.base_currency", "USD", False, "str"),
    "commercial.min_withdrawal_minor": SettingSpec(
        "commercial.min_withdrawal_minor", 1000, False, "int"
    ),
    "commercial.max_withdrawal_minor": SettingSpec(
        "commercial.max_withdrawal_minor", 100_000_000, False, "int"
    ),
    "payout.hold_days": SettingSpec("payout.hold_days", 15, False, "int"),
    "payout.sla_business_days": SettingSpec("payout.sla_business_days", 2, False, "int"),
    "telephony.default_timeout_seconds": SettingSpec(
        "telephony.default_timeout_seconds", 30, False, "int"
    ),
    "telephony.stt_provider": SettingSpec("telephony.stt_provider", "", False, "str"),
    "telephony.tts_provider": SettingSpec("telephony.tts_provider", "", False, "str"),
    "telephony.llm_provider": SettingSpec("telephony.llm_provider", "", False, "str"),
    "telephony.stt_api_key_ref": SettingSpec(
        "telephony.stt_api_key_ref", "VOICE_STT_API_KEY", True, "str"
    ),
    "telephony.tts_api_key_ref": SettingSpec(
        "telephony.tts_api_key_ref", "VOICE_TTS_API_KEY", True, "str"
    ),
    "telephony.llm_api_key_ref": SettingSpec(
        "telephony.llm_api_key_ref", "VOICE_LLM_API_KEY", True, "str"
    ),
    "ai.default_voice": SettingSpec("ai.default_voice", "", False, "str"),
    "compliance.recording_retention_days": SettingSpec(
        "compliance.recording_retention_days", 30, False, "int"
    ),
    "compliance.recording_disclosure": SettingSpec(
        "compliance.recording_disclosure", "required", False, "str"
    ),
    "compliance.kyc_gate": SettingSpec("compliance.kyc_gate", True, False, "bool"),
    "notifications.email_sender": SettingSpec(
        "notifications.email_sender", "noreply@vokit.test", False, "str"
    ),
    "security.session_seconds": SettingSpec("security.session_seconds", 1_209_600, False, "int"),
    "security.mfa_required_privileged": SettingSpec(
        "security.mfa_required_privileged", False, False, "bool"
    ),
    "flags.recordings_live": SettingSpec("flags.recordings_live", False, False, "bool"),
    "flags.calling_live": SettingSpec("flags.calling_live", False, False, "bool"),
    "flags.billing_live": SettingSpec("flags.billing_live", False, False, "bool"),
    "flags.integrations": SettingSpec("flags.integrations", True, False, "bool"),
    "flags.outbound": SettingSpec("flags.outbound", True, False, "bool"),
    "flags.customer_edit": SettingSpec("flags.customer_edit", False, False, "bool"),
    "flags.templates": SettingSpec("flags.templates", True, False, "bool"),
}
