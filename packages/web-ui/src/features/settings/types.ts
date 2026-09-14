export type SettingRow = {
  key: string;
  value?: unknown;
  secret?: boolean;
  has_value?: boolean;
};

export type AgencyFlag = {
  agency_id?: string;
  flag?: string;
  enabled?: boolean;
};

export type SettingsSnapshot = {
  settings?: SettingRow[];
  agency_flags?: AgencyFlag[];
};

export const FEATURE_FLAGS = [
  "recordings_live",
  "calling_live",
  "billing_live",
  "integrations",
  "outbound",
  "customer_edit",
  "templates",
] as const;

export const SETTING_GROUPS: Array<{
  id: string;
  label: string;
  keys: string[];
}> = [
  {
    id: "currency",
    label: "Currency",
    keys: [
      "commercial.base_currency",
      "commercial.min_withdrawal_minor",
      "commercial.max_withdrawal_minor",
    ],
  },
  {
    id: "business",
    label: "Business days / payout SLA",
    keys: ["payout.hold_days", "payout.sla_business_days"],
  },
  {
    id: "providers",
    label: "Provider settings",
    keys: [
      "telephony.default_timeout_seconds",
      "telephony.stt_provider",
      "telephony.tts_provider",
      "telephony.llm_provider",
      "telephony.stt_model",
      "telephony.tts_model",
      "telephony.llm_model",
      "voice.deepgram.api_key",
      "voice.cartesia.api_key",
      "voice.elevenlabs.api_key",
      "voice.openai.api_key",
      "voice.grok.api_key",
      "voice.anthropic.api_key",
      "ai.default_voice",
      "notifications.email_sender",
    ],
  },
  {
    id: "flags",
    label: "Feature flags (global)",
    keys: [
      "flags.recordings_live",
      "flags.calling_live",
      "flags.billing_live",
      "flags.integrations",
      "flags.outbound",
      "flags.customer_edit",
      "flags.templates",
    ],
  },
  {
    id: "compliance",
    label: "Compliance",
    keys: [
      "compliance.recording_retention_days",
      "compliance.recording_disclosure",
      "compliance.kyc_gate",
    ],
  },
  {
    id: "security",
    label: "Security",
    keys: ["security.mfa_required_privileged"],
  },
];
