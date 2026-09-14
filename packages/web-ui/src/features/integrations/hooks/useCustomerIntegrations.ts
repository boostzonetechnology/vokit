import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import type { IntegrationConnection } from "@/features/integrations/types";
import { asList } from "@/features/platform/lib/list";
import { AGENCY_PROVIDERS } from "@/features/integrations/hooks/useAgencyIntegrations";

export function useCustomerIntegrations() {
  const [connections, setConnections] = useState<IntegrationConnection[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [selfServiceBlocked, setSelfServiceBlocked] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = asList<IntegrationConnection>(
        await apiGet<unknown>("/api/v1/customer/integrations"),
      );
      setConnections(rows);
      setSelfServiceBlocked(false);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load integrations.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return connections;
    return connections.filter((row) =>
      [row.provider, row.display_name, row.status, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [connections, query]);

  const selected = connections.find((row) => row.id === selectedId) ?? null;

  async function connect(input: {
    provider: string;
    credential: string;
    display_name: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<IntegrationConnection>(
        "/api/v1/customer/integrations",
        "POST",
        input,
      );
      setSelfServiceBlocked(false);
      setMessage("Connection saved. Credential will not be shown again.");
      await reload();
      if (created.id) setSelectedId(created.id);
      return created;
    } catch (cause) {
      const text = isApiError(cause) ? cause.message : "Connect failed.";
      setMessage(text);
      if (/self.?service|not permitted|forbidden/i.test(text)) {
        setSelfServiceBlocked(true);
      }
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function testConnection(connectionId: string) {
    setBusy(true);
    setMessage("");
    try {
      const result = await apiSend<{ ok?: boolean; error?: string; status?: string }>(
        `/api/v1/customer/integrations/${connectionId}/test`,
        "POST",
        {},
      );
      setMessage(
        result.ok === false || result.error
          ? `Test failed: ${result.error || result.status || "unknown"}`
          : "Connection test succeeded.",
      );
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Test failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    providers: AGENCY_PROVIDERS,
    connections: filtered,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    selfServiceBlocked,
    reload,
    connect,
    testConnection,
  };
}
