import { useCallback, useEffect, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import type { GlobalInstructionsPayload } from "@/features/instructions/types";

export function usePlatformInstructions() {
  const [body, setBody] = useState("");
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiGet<GlobalInstructionsPayload | string>(
        "/api/v1/platform/instructions",
      );
      const next =
        typeof data === "string"
          ? data
          : typeof data?.body === "string"
            ? data.body
            : "";
      setBody(next);
      setDraft(next);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load instructions.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function saveGlobal() {
    setBusy(true);
    setMessage("");
    try {
      await apiSend("/api/v1/platform/instructions", "POST", { body: draft });
      setMessage("Global instructions saved. A new revision is stored server-side.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Save failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    body,
    draft,
    setDraft,
    error,
    message,
    loading,
    busy,
    reload,
    saveGlobal,
    dirty: draft !== body,
  };
}
