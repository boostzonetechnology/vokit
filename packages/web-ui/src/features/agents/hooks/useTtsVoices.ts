import { useCallback, useEffect, useState } from "react";

import { isApiError, type Portal } from "@/api";
import {
  getTtsVoices,
  type TtsVoiceOption,
} from "@/features/agents/services/ttsVoices.service";

function mapTtsError(cause: unknown): string {
  if (!isApiError(cause)) {
    return "Failed to load TTS voices.";
  }
  if (cause.status === 503 || cause.code === "voice_provider_not_configured" || cause.code === "secret_missing") {
    return (
      cause.message ||
      "TTS provider or API key is not configured. Ask a Super Admin to set Providers in platform settings."
    );
  }
  if (cause.status === 502 || cause.code === "provider_unavailable") {
    return cause.message || "Voice vendor is unavailable. Try again later.";
  }
  return cause.message || "Failed to load TTS voices.";
}

export function useTtsVoices(portal: Portal) {
  const [provider, setProvider] = useState("");
  const [voices, setVoices] = useState<TtsVoiceOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getTtsVoices(portal);
      setProvider(data.provider);
      setVoices(data.voices);
    } catch (cause) {
      setProvider("");
      setVoices([]);
      setError(mapTtsError(cause));
    } finally {
      setLoading(false);
    }
  }, [portal]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { provider, voices, loading, error, reload };
}
