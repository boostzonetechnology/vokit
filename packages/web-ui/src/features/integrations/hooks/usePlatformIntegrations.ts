import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { IntegrationConnection, IntegrationProvider } from "@/features/integrations/types";

export function usePlatformIntegrations() {
  const [providers, setProviders] = useState<IntegrationProvider[]>([]);
  const [connections, setConnections] = useState<IntegrationConnection[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [agencyFilter, setAgencyFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (agencyFilter.trim()) params.set("agency_id", agencyFilter.trim());
      const qs = params.toString();
      const [providerRows, connectionRows] = await Promise.all([
        asList<IntegrationProvider>(
          await apiGet<unknown>("/api/v1/platform/integration-providers"),
        ),
        asList<IntegrationConnection>(
          await apiGet<unknown>(`/api/v1/platform/integrations${qs ? `?${qs}` : ""}`),
        ),
      ]);
      setProviders(providerRows);
      setConnections(connectionRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load integrations.");
    } finally {
      setLoading(false);
    }
  }, [agencyFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return connections;
    return connections.filter((row) =>
      [row.provider, row.display_name, row.status, row.agency_id, row.customer_id, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [connections, query]);

  const selected = connections.find((row) => row.id === selectedId) ?? null;

  async function disableConnection(connectionId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/integrations/${connectionId}/disable`, "POST", {});
      setMessage("Connection disabled.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Disable failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    providers,
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
    agencyFilter,
    setAgencyFilter,
    reload,
    disableConnection,
  };
}
