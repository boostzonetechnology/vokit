import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { CallArtifact, CallRecord } from "@/features/calls/types";

export type CustomerOption = {
  id: string;
  display_name?: string;
};

export type AgentOption = {
  id: string;
  display_name?: string;
  customer_id?: string;
};

export function useAgencyCalls() {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [artifacts, setArtifacts] = useState<CallArtifact[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");
  const [agentFilter, setAgentFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [directionFilter, setDirectionFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (customerFilter) params.set("customer_id", customerFilter);
      const qs = params.toString();
      const [callRows, customerRows, agentRows] = await Promise.all([
        apiGet<unknown>(`/api/v1/agency/calls${qs ? `?${qs}` : ""}`).then((data) =>
          asList<CallRecord>(data),
        ),
        apiGet<unknown>("/api/v1/agency/customers")
          .then((data) => asList<CustomerOption>(data))
          .catch(() => [] as CustomerOption[]),
        apiGet<unknown>("/api/v1/agency/agents")
          .then((data) => asList<AgentOption>(data))
          .catch(() => [] as AgentOption[]),
      ]);
      setCalls(callRows);
      setCustomers(customerRows);
      setAgents(agentRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load calls.");
    } finally {
      setLoading(false);
    }
  }, [customerFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return calls.filter((row) => {
      if (agentFilter && row.agent_id !== agentFilter) return false;
      if (statusFilter && (row.status ?? "") !== statusFilter) return false;
      if (directionFilter && (row.direction ?? "") !== directionFilter) return false;
      if (!q) return true;
      return [row.e164, row.remote_e164, row.status, row.end_reason, row.id, row.edge_call_id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [calls, query, agentFilter, statusFilter, directionFilter]);

  const selected = filtered.find((row) => row.id === selectedId) ?? null;

  async function loadArtifacts(callId: string) {
    setBusy(true);
    setMessage("");
    try {
      const rows = asList<CallArtifact>(
        await apiGet<unknown>(`/api/v1/agency/calls/${callId}/artifacts`),
      );
      setArtifacts(rows);
      if (!rows.length) {
        setMessage("No recording/transcript artifacts for this call yet.");
      }
    } catch (cause) {
      setArtifacts([]);
      setMessage(
        isApiError(cause)
          ? cause.message
          : "Artifacts unavailable — check customer agreement and recordings permission.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function grantAccess(callId: string, artifactId: string) {
    setBusy(true);
    try {
      await apiSend(
        `/api/v1/agency/calls/${callId}/artifacts/${artifactId}/access`,
        "POST",
        {},
      );
      setMessage("Short-lived artifact access granted. Playback opens via recording plane.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Access grant failed.");
    } finally {
      setBusy(false);
    }
  }

  function customerName(customerId?: string) {
    if (!customerId) return "—";
    return customers.find((row) => row.id === customerId)?.display_name || customerId.slice(0, 8);
  }

  function agentName(agentId?: string) {
    if (!agentId) return "—";
    return agents.find((row) => row.id === agentId)?.display_name || agentId.slice(0, 8);
  }

  return {
    calls: filtered,
    artifacts,
    customers,
    agents,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    customerFilter,
    setCustomerFilter,
    agentFilter,
    setAgentFilter,
    statusFilter,
    setStatusFilter,
    directionFilter,
    setDirectionFilter,
    customerName,
    agentName,
    reload,
    loadArtifacts,
    grantAccess,
  };
}
