import { useCallback, useEffect, useState } from "react";

import { apiGet, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { AuditEvent } from "@/features/audit/types";

export type AuditFilters = {
  actor_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  agency_id: string;
  customer_id: string;
  ip: string;
  severity: string;
  since: string;
  until: string;
};

const EMPTY_FILTERS: AuditFilters = {
  actor_id: "",
  action: "",
  entity_type: "",
  entity_id: "",
  agency_id: "",
  customer_id: "",
  ip: "",
  severity: "",
  since: "",
  until: "",
};

export function usePlatformAudit() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [filters, setFilters] = useState<AuditFilters>(EMPTY_FILTERS);
  const [applied, setApplied] = useState<AuditFilters>(EMPTY_FILTERS);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      (Object.keys(applied) as Array<keyof AuditFilters>).forEach((key) => {
        const value = applied[key].trim();
        if (value) params.set(key, value);
      });
      const qs = params.toString();
      const rows = asList<AuditEvent>(
        await apiGet<unknown>(`/api/v1/platform/audit-events${qs ? `?${qs}` : ""}`),
      );
      setEvents(rows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load audit events.");
    } finally {
      setLoading(false);
    }
  }, [applied]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const selected = events.find((row) => row.id === selectedId) ?? null;

  function applyFilters() {
    setApplied({ ...filters });
  }

  function resetFilters() {
    setFilters(EMPTY_FILTERS);
    setApplied(EMPTY_FILTERS);
  }

  return {
    events,
    selected,
    selectedId,
    setSelectedId,
    filters,
    setFilters,
    error,
    loading,
    reload,
    applyFilters,
    resetFilters,
  };
}
