import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { CallArtifact, CallRecord } from "@/features/calls/types";

export function usePlatformCalls() {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [artifacts, setArtifacts] = useState<CallArtifact[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [agencyFilter, setAgencyFilter] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");
  const [agentFilter, setAgentFilter] = useState("");
  const [numberFilter, setNumberFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [directionFilter, setDirectionFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (agencyFilter.trim()) params.set("agency_id", agencyFilter.trim());
      if (customerFilter.trim()) params.set("customer_id", customerFilter.trim());
      const qs = params.toString();
      const rows = asList<CallRecord>(
        await apiGet<unknown>(`/api/v1/platform/calls${qs ? `?${qs}` : ""}`),
      );
      setCalls(rows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load calls.");
    } finally {
      setLoading(false);
    }
  }, [agencyFilter, customerFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    return calls.filter((row) => {
      if (agentFilter && !(row.agent_id ?? "").includes(agentFilter.trim())) return false;
      if (statusFilter && (row.status ?? "") !== statusFilter) return false;
      if (directionFilter && (row.direction ?? "") !== directionFilter) return false;
      if (numberFilter.trim()) {
        const q = numberFilter.trim().toLowerCase();
        const hay = `${row.e164 ?? ""} ${row.remote_e164 ?? ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [calls, agentFilter, statusFilter, directionFilter, numberFilter]);

  const selected = filtered.find((row) => row.id === selectedId) ?? null;

  async function loadArtifacts(callId: string) {
    setBusy(true);
    setMessage("");
    try {
      const rows = asList<CallArtifact>(
        await apiGet<unknown>(`/api/v1/platform/calls/${callId}/artifacts`),
      );
      setArtifacts(rows);
    } catch (cause) {
      setArtifacts([]);
      setMessage(
        isApiError(cause)
          ? cause.message
          : "Artifacts require recordings.review and may be empty.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function grantAccess(callId: string, artifactId: string) {
    setBusy(true);
    try {
      await apiSend(
        `/api/v1/platform/calls/${callId}/artifacts/${artifactId}/access`,
        "POST",
        {},
      );
      setMessage("Artifact access granted.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Access grant failed.");
    } finally {
      setBusy(false);
    }
  }

  return {
    calls: filtered,
    artifacts,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    agencyFilter,
    setAgencyFilter,
    customerFilter,
    setCustomerFilter,
    agentFilter,
    setAgentFilter,
    numberFilter,
    setNumberFilter,
    statusFilter,
    setStatusFilter,
    directionFilter,
    setDirectionFilter,
    reload,
    loadArtifacts,
    grantAccess,
  };
}
