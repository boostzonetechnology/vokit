import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { CallIndexRow, TransferDestination } from "@/features/transfers/types";

export function usePlatformTransfers() {
  const [destinations, setDestinations] = useState<TransferDestination[]>([]);
  const [failedCalls, setFailedCalls] = useState<CallIndexRow[]>([]);
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
      const rows = asList<TransferDestination>(
        await apiGet<unknown>("/api/v1/platform/transfers"),
      );
      let calls: CallIndexRow[] = [];
      try {
        calls = asList<CallIndexRow>(await apiGet<unknown>("/api/v1/platform/calls"));
      } catch {
        calls = [];
      }
      setDestinations(rows);
      setFailedCalls(
        calls.filter((row) => {
          const status = (row.status ?? "").toLowerCase();
          const reason = (row.end_reason ?? "").toLowerCase();
          return (
            status.includes("fail") ||
            reason.includes("transfer") ||
            reason.includes("disabled") ||
            reason.includes("no_answer")
          );
        }),
      );
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load transfers.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return destinations.filter((row) => {
      if (statusFilter === "disabled" && !row.platform_disabled && row.status !== "disabled") {
        return false;
      }
      if (statusFilter === "active" && (row.platform_disabled || row.status === "disabled")) {
        return false;
      }
      if (!q) return true;
      return [row.label, row.kind, row.status, row.agency_id, row.customer_id, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [destinations, query, statusFilter]);

  const selected = destinations.find((row) => row.id === selectedId) ?? null;

  async function disableDestination(destinationId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/transfers/${destinationId}/disable`, "POST", {
        confirm: true,
      });
      setMessage("Transfer destination disabled.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Disable failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    destinations: filtered,
    failedCalls,
    selected,
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
    disableDestination,
  };
}
