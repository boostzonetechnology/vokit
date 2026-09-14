import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import type { CallArtifact, CallRecord } from "@/features/calls/types";
import { asList } from "@/features/platform/lib/list";

export type AgentOption = {
  id: string;
  display_name?: string;
};

export function useCustomerCalls() {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [artifacts, setArtifacts] = useState<CallArtifact[]>([]);
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [agentFilter, setAgentFilter] = useState("");
  const [directionFilter, setDirectionFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [numberFilter, setNumberFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [callRows, agentRows] = await Promise.all([
        asList<CallRecord>(await apiGet<unknown>("/api/v1/customer/calls")),
        apiGet<unknown>("/api/v1/customer/agents")
          .then((data) => asList<AgentOption>(data))
          .catch(() => [] as AgentOption[]),
      ]);
      setCalls(callRows);
      setAgents(agentRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load calls.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const numberQ = numberFilter.trim().toLowerCase();
    return calls.filter((row) => {
      if (agentFilter && row.agent_id !== agentFilter) return false;
      if (directionFilter && (row.direction ?? "") !== directionFilter) return false;
      if (statusFilter && (row.status ?? "") !== statusFilter) return false;
      if (numberQ) {
        const hay = `${row.e164 ?? ""} ${row.remote_e164 ?? ""}`.toLowerCase();
        if (!hay.includes(numberQ)) return false;
      }
      if (!q) return true;
      return [row.e164, row.remote_e164, row.status, row.end_reason, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [calls, query, agentFilter, directionFilter, statusFilter, numberFilter]);

  const selected = filtered.find((row) => row.id === selectedId) ?? null;

  async function loadArtifacts(callId: string) {
    setBusy(true);
    setMessage("");
    try {
      const rows = asList<CallArtifact>(
        await apiGet<unknown>(`/api/v1/customer/calls/${callId}/artifacts`),
      );
      setArtifacts(rows);
      if (!rows.length) setMessage("No artifacts for this call yet.");
    } catch (cause) {
      setArtifacts([]);
      setMessage(isApiError(cause) ? cause.message : "Artifacts unavailable.");
    } finally {
      setBusy(false);
    }
  }

  async function grantAccess(callId: string, artifactId: string) {
    setBusy(true);
    try {
      await apiSend(
        `/api/v1/customer/calls/${callId}/artifacts/${artifactId}/access`,
        "POST",
        {},
      );
      setMessage("Short-lived artifact access granted.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Access grant failed.");
    } finally {
      setBusy(false);
    }
  }

  function exportCsv() {
    const header = [
      "id",
      "direction",
      "status",
      "e164",
      "remote_e164",
      "agent_id",
      "end_reason",
      "started_at",
      "duration_seconds",
      "billed_minutes",
    ];
    const lines = [
      header.join(","),
      ...filtered.map((row) =>
        [
          row.id,
          row.direction,
          row.status,
          row.e164,
          row.remote_e164,
          row.agent_id,
          row.end_reason,
          row.started_at,
          row.duration_seconds,
          row.billed_minutes,
        ]
          .map((value) => `"${String(value ?? "").replaceAll('"', '""')}"`)
          .join(","),
      ),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `customer-calls-${new Date().toISOString().slice(0, 10)}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    setMessage("CSV export downloaded (client-side).");
  }

  function agentName(agentId?: string) {
    if (!agentId) return "—";
    return agents.find((row) => row.id === agentId)?.display_name || agentId.slice(0, 8);
  }

  return {
    calls: filtered,
    artifacts,
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
    agentFilter,
    setAgentFilter,
    directionFilter,
    setDirectionFilter,
    statusFilter,
    setStatusFilter,
    numberFilter,
    setNumberFilter,
    agentName,
    reload,
    loadArtifacts,
    grantAccess,
    exportCsv,
  };
}
