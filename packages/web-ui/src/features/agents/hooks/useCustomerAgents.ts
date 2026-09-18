import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend } from "@/api";
import { mapAgentError } from "@/features/agents/lib/mapAgentError";
import { asList } from "@/features/platform/lib/list";
import type { CustomerAgentDetail, CustomerAgentRow } from "@/features/agents/types";

export function useCustomerAgents() {
  const [agents, setAgents] = useState<CustomerAgentRow[]>([]);
  const [detail, setDetail] = useState<CustomerAgentDetail | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
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
      setError(mapAgentError(cause, "Failed to load agents."));
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
      return null;
    }
    setDetailLoading(true);
    try {
      const row = await apiGet<CustomerAgentDetail>(`/api/v1/customer/agents/${agentId}`);
      setDetail(row);
      return row;
    } catch (cause) {
      setDetail(null);
      setMessage(mapAgentError(cause, "Failed to load agent detail."));
      return null;
    } finally {
      setDetailLoading(false);
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
      return [row.display_name, row.status, row.id, row.assigned_e164, row.agent_type]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [agents, query, statusFilter]);

  const statusOptions = useMemo(
    () => [...new Set(agents.map((row) => (row.status ?? "").toLowerCase()).filter(Boolean))],
    [agents],
  );

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
      setMessage(mapAgentError(cause, "Update failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function pauseAgent(agentId = selectedId) {
    if (!agentId) return;
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<CustomerAgentDetail>(
        `/api/v1/customer/agents/${agentId}/pause`,
        "POST",
        {},
      );
      setDetail(updated);
      setMessage("Agent paused.");
      await reload();
    } catch (cause) {
      setMessage(mapAgentError(cause, "Pause failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function resumeAgent(agentId = selectedId) {
    if (!agentId) return;
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<CustomerAgentDetail>(
        `/api/v1/customer/agents/${agentId}/resume`,
        "POST",
        {},
      );
      setDetail(updated);
      setMessage("Agent resumed.");
      await reload();
    } catch (cause) {
      setMessage(mapAgentError(cause, "Resume failed."));
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
    detailLoading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    statusOptions,
    reload,
    saveLimitedFields,
    pauseAgent,
    resumeAgent,
  };
}
