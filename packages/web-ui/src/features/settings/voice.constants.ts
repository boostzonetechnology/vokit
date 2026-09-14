/** Allowlists aligned with backend voice_catalog (VOICE-PROVIDERS.md). */

export const STT_TTS_PROVIDERS = ["deepgram", "elevenlabs", "cartesia"] as const;
export const LLM_PROVIDERS = ["openai", "grok", "anthropic"] as const;

export type SttTtsProvider = (typeof STT_TTS_PROVIDERS)[number];
export type LlmProvider = (typeof LLM_PROVIDERS)[number];
export type VoiceVendorCode = SttTtsProvider | LlmProvider;
export type VoiceCapability = "stt" | "tts" | "llm";

export const VOICE_API_KEY_KEYS = [
  "voice.deepgram.api_key",
  "voice.cartesia.api_key",
  "voice.elevenlabs.api_key",
  "voice.openai.api_key",
  "voice.grok.api_key",
  "voice.anthropic.api_key",
] as const;

export type VoiceApiKeyKey = (typeof VOICE_API_KEY_KEYS)[number];

export type VendorCardDef = {
  code: VoiceVendorCode;
  title: string;
  capabilities: VoiceCapability[];
  apiKeyKey: VoiceApiKeyKey;
};

/** One card per vendor — capabilities match backend allowlists (no embedding in V1). */
export const VENDOR_CARDS: VendorCardDef[] = [
  {
    code: "deepgram",
    title: "Deepgram",
    capabilities: ["stt", "tts"],
    apiKeyKey: "voice.deepgram.api_key",
  },
  {
    code: "elevenlabs",
    title: "ElevenLabs",
    capabilities: ["stt", "tts"],
    apiKeyKey: "voice.elevenlabs.api_key",
  },
  {
    code: "cartesia",
    title: "Cartesia",
    capabilities: ["stt", "tts"],
    apiKeyKey: "voice.cartesia.api_key",
  },
  {
    code: "openai",
    title: "OpenAI",
    capabilities: ["llm"],
    apiKeyKey: "voice.openai.api_key",
  },
  {
    code: "grok",
    title: "Grok",
    capabilities: ["llm"],
    apiKeyKey: "voice.grok.api_key",
  },
  {
    code: "anthropic",
    title: "Anthropic Claude",
    capabilities: ["llm"],
    apiKeyKey: "voice.anthropic.api_key",
  },
];

export const CAPABILITY_PROVIDER_KEY: Record<VoiceCapability, string> = {
  stt: "telephony.stt_provider",
  tts: "telephony.tts_provider",
  llm: "telephony.llm_provider",
};

export const CAPABILITY_MODEL_KEY: Record<VoiceCapability, string> = {
  stt: "telephony.stt_model",
  tts: "telephony.tts_model",
  llm: "telephony.llm_model",
};

const PROVIDER_SELECT_KEYS = new Set(Object.values(CAPABILITY_PROVIDER_KEY));

export function isProviderSelectKey(key: string): boolean {
  return PROVIDER_SELECT_KEYS.has(key);
}

export function isVoiceApiKeyKey(key: string): boolean {
  return (VOICE_API_KEY_KEYS as readonly string[]).includes(key);
}

export function optionsForProviderKey(key: string): readonly string[] {
  if (key === "telephony.llm_provider") return LLM_PROVIDERS;
  if (key === "telephony.stt_provider" || key === "telephony.tts_provider") {
    return STT_TTS_PROVIDERS;
  }
  return [];
}

export function capabilityLabel(cap: VoiceCapability): string {
  return cap.toUpperCase();
}
