import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";

export type CustomerAgentRow = {
  id: string;
  display_name?: string;
  status?: string;
  customer_id?: string;
  agency_id?: string;
};

export type CustomerAgentDetail = CustomerAgentRow & {
  agent_type?: string;
  timezone?: string;
  voice_provider?: string;
  voice_id?: string;
  language?: string;
  greeting?: string;
  instructions?: string;
  inbound_enabled?: boolean;
  outbound_enabled?: boolean;
  recording_disclosure?: boolean;
  customer_can_edit?: boolean;
  published_version?: number | null;
  production_routable?: boolean;
  e164?: string;
};

export function useCustomerAgents() {
  const [agents, setAgents] = useState<CustomerAgentRow[]>([]);
  const [detail, setDetail] = useState<CustomerAgentDetail | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = asList<CustomerAgentRow>(await apiGet<unknown>("/api/v1/customer/agents"));
      setAgents(rows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load agents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const loadDetail = useCallback(async (agentId: string) => {
    if (!agentId) {
      setDetail(null);
      return;
    }
    setBusy(true);
    try {
      const row = await apiGet<CustomerAgentDetail>(`/api/v1/customer/agents/${agentId}`);
      setDetail(row);
    } catch (cause) {
      setDetail(null);
      setMessage(isApiError(cause) ? cause.message : "Failed to load agent detail.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (selectedId) void loadDetail(selectedId);
  }, [selectedId, loadDetail]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return agents.filter((row) => {
      if (statusFilter && (row.status ?? "").toLowerCase() !== statusFilter) return false;
      if (!q) return true;
      return [row.display_name, row.status, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [agents, query, statusFilter]);

  async function saveLimitedFields(input: { greeting: string; instructions: string }) {
    if (!selectedId || !detail?.customer_can_edit) {
      throw new Error("Editing is not permitted for this agent.");
    }
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<CustomerAgentDetail>(
        `/api/v1/customer/agents/${selectedId}`,
        "PATCH",
        {
          greeting: input.greeting,
          instructions: input.instructions,
        },
      );
      setDetail(updated);
      setMessage("Allowed fields updated.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Update failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    agents: filtered,
    detail,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    reload,
    saveLimitedFields,
  };
}
