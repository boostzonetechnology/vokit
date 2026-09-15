import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { safeGetList } from "@/features/platform/lib/list";
import type {
  AgencyOption,
  CustomerOption,
  PhoneNumberRow,
  PlatformAgentDetail,
  PlatformAgentDiagnostics,
  PlatformAgentRow,
} from "@/features/agents/types";

export function usePlatformAgentsDirectory() {
  const [agents, setAgents] = useState<PlatformAgentRow[]>([]);
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [numbers, setNumbers] = useState<PhoneNumberRow[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<PlatformAgentDetail | null>(null);
  const [diagnostics, setDiagnostics] = useState<PlatformAgentDiagnostics | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [diagnosticsLoading, setDiagnosticsLoading] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [agentRows, agencyRows, customerRows, numberRows] = await Promise.all([
        safeGetList<PlatformAgentRow>("/api/v1/platform/agents", apiGet, [
          "results",
          "items",
          "agents",
        ]),
        safeGetList<AgencyOption>("/api/v1/platform/agencies", apiGet),
        safeGetList<CustomerOption>("/api/v1/platform/customers", apiGet),
        safeGetList<PhoneNumberRow>("/api/v1/platform/phone-numbers", apiGet),
      ]);
      setAgents(agentRows);
      setAgencies(agencyRows);
      setCustomers(customerRows);
      setNumbers(numberRows);
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

  const agencyName = useMemo(() => {
    const map = new Map(
      agencies.map((row) => [row.id, row.display_name || row.id.slice(0, 8)]),
    );
    return (id?: string) => (id ? map.get(id) ?? id.slice(0, 8) : "—");
  }, [agencies]);

  const customerName = useMemo(() => {
    const map = new Map(
      customers.map((row) => [row.id, row.display_name || row.id.slice(0, 8)]),
    );
    return (id?: string) => (id ? map.get(id) ?? id.slice(0, 8) : "—");
  }, [customers]);

  const numberByAgent = useMemo(() => {
    const map = new Map<string, string>();
    for (const row of agents) {
      if (row.assigned_e164) {
        map.set(row.id, row.assigned_e164);
      }
    }
    for (const row of numbers) {
      if (row.assigned_agent_id && row.e164 && !map.has(row.assigned_agent_id)) {
        map.set(row.assigned_agent_id, row.e164);
      }
    }
    return map;
  }, [agents, numbers]);

  const loadAgentDetail = useCallback(async (agentId: string) => {
    setDetailLoading(true);
    try {
      const detail = await apiGet<PlatformAgentDetail>(
        `/api/v1/platform/agents/${agentId}`,
      );
      setSelectedDetail(detail);
      return detail;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Failed to load agent detail.");
      setSelectedDetail(null);
      return null;
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const loadDiagnostics = useCallback(async (agentId: string) => {
    setDiagnosticsLoading(true);
    try {
      const data = await apiGet<PlatformAgentDiagnostics>(
        `/api/v1/platform/agents/${agentId}/diagnostics`,
      );
      setDiagnostics(data);
      return data;
    } catch (cause) {
      setDiagnostics(null);
      setMessage(isApiError(cause) ? cause.message : "Failed to load diagnostics.");
      return null;
    } finally {
      setDiagnosticsLoading(false);
    }
  }, []);

  const clearSelectionSideState = useCallback(() => {
    setSelectedDetail(null);
    setDiagnostics(null);
  }, []);

  async function createAgent(input: { customer_id: string; display_name: string }) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend("/api/v1/platform/agents", "POST", input);
      setMessage("Agent draft created.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function configureAgent(agentId: string, patch: Record<string, unknown>) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<PlatformAgentDetail>(
        `/api/v1/platform/agents/${agentId}`,
        "PATCH",
        patch,
      );
      setSelectedDetail(updated);
      setMessage("Agent configuration saved.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Configure failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function publishAgent(agentId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/agents/${agentId}/publish`, "POST", {});
      setMessage("Agent published.");
      await reload();
      await loadAgentDetail(agentId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Publish failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function pauseAgent(agentId: string, reason: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/agents/${agentId}/pause`, "POST", { reason });
      setMessage("Agent paused (status locked for agency).");
      await reload();
      await loadAgentDetail(agentId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Pause failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function archiveAgent(agentId: string, reason: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/agents/${agentId}/archive`, "POST", { reason });
      setMessage("Agent archived.");
      await reload();
      await loadAgentDetail(agentId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Archive failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function disableAgent(agentId: string, reason: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/agents/${agentId}/disable`, "POST", { reason });
      setMessage("Agent disabled (suspended + locked).");
      await reload();
      await loadAgentDetail(agentId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Disable failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function restoreAgent(agentId: string, status = "active") {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/agents/${agentId}/status`, "POST", { status });
      setMessage(`Agent restored to ${status}.`);
      await reload();
      await loadAgentDetail(agentId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Restore failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function cloneAgent(
    agentId: string,
    input: { customer_id: string; display_name?: string },
  ) {
    setBusy(true);
    setMessage("");
    try {
      const body: Record<string, string> = { customer_id: input.customer_id };
      if (input.display_name?.trim()) body.display_name = input.display_name.trim();
      await apiSend(`/api/v1/platform/agents/${agentId}/clone`, "POST", body);
      setMessage("Agent cloned as a new draft.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Clone failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    agents,
    agencies,
    customers,
    selectedDetail,
    diagnostics,
    agencyName,
    customerName,
    numberByAgent,
    error,
    message,
    setMessage,
    loading,
    busy,
    detailLoading,
    diagnosticsLoading,
    reload,
    loadAgentDetail,
    loadDiagnostics,
    clearSelectionSideState,
    createAgent,
    configureAgent,
    publishAgent,
    pauseAgent,
    archiveAgent,
    disableAgent,
    restoreAgent,
    cloneAgent,
  };
}
