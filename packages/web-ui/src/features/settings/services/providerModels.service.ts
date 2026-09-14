import { apiGet } from "@/api";
import type { VoiceCapability, VoiceVendorCode } from "@/features/settings/voice.constants";

export type ProviderModelOption = {
  id: string;
  name: string;
};

export type ProviderModelsPayload = {
  provider: string;
  capability: VoiceCapability;
  models: ProviderModelOption[];
};

export async function getProviderModels(
  vendor: VoiceVendorCode,
  capability: VoiceCapability,
): Promise<ProviderModelsPayload> {
  const data = await apiGet<ProviderModelsPayload>(
    `/api/v1/platform/providers/${vendor}/models?capability=${capability}`,
  );
  return {
    provider: data.provider || vendor,
    capability,
    models: Array.isArray(data.models) ? data.models : [],
  };
}
