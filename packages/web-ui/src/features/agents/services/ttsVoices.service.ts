import { apiGet, type Portal } from "@/api";

export type TtsVoiceOption = {
  id: string;
  name: string;
  language?: string | null;
};

export type TtsVoicesPayload = {
  provider: string;
  voices: TtsVoiceOption[];
};

export async function getTtsVoices(portal: Portal): Promise<TtsVoicesPayload> {
  const data = await apiGet<TtsVoicesPayload>(`/api/v1/${portal}/tts/voices`);
  return {
    provider: data.provider || "",
    voices: Array.isArray(data.voices) ? data.voices : [],
  };
}
