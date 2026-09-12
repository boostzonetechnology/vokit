import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { TransferDestination } from "@/features/transfers/types";

export type CustomerOption = {
  id: string;
  display_name?: string;
};

export type CreateDestinationInput = {
  customer_id: string;
  kind: string;
  label: string;
  target: string;
  no_answer_seconds: number;
  members?: Array<{ kind: string; target: string; label?: string }>;
};

export function useAgencyTransfers() {
  const [destinations, setDestinations] = useState<TransferDestination[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (customerFilter) params.set("customer_id", customerFilter);
      const qs = params.toString();
      const [rows, customerRows] = await Promise.all([
        apiGet<unknown>(`/api/v1/agency/transfers${qs ? `?${qs}` : ""}`).then((data) =>
          asList<TransferDestination>(data),
        ),
        apiGet<unknown>("/api/v1/agency/customers")
          .then((data) => asList<CustomerOption>(data))
          .catch(() => [] as CustomerOption[]),
      ]);
      setDestinations(rows);
      setCustomers(customerRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load transfer destinations.");
    } finally {
      setLoading(false);
    }
  }, [customerFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return destinations.filter((row) => {
      if (statusFilter === "disabled" && row.status !== "disabled" && !row.platform_disabled) {
        return false;
      }
      if (statusFilter === "active" && (row.status === "disabled" || row.platform_disabled)) {
        return false;
      }
      if (!q) return true;
      return [row.label, row.kind, row.target, row.status, row.customer_id, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [destinations, query, statusFilter]);

  const selected = destinations.find((row) => row.id === selectedId) ?? null;

  async function createDestination(input: CreateDestinationInput) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<TransferDestination>("/api/v1/agency/transfers", "POST", {
        customer_id: input.customer_id,
        kind: input.kind,
        label: input.label,
        target: input.target,
        no_answer_seconds: input.no_answer_seconds,
        members: input.members ?? [],
      });
      setMessage("Transfer destination created.");
      await reload();
      if (created.id) setSelectedId(created.id);
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function disableDestination(destinationId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/transfers/${destinationId}/disable`, "POST", {});
      setMessage("Destination disabled.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Disable failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  function customerName(customerId?: string) {
    if (!customerId) return "—";
    return customers.find((row) => row.id === customerId)?.display_name || customerId.slice(0, 8);
  }

  return {
    destinations: filtered,
    customers,
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
    statusFilter,
    setStatusFilter,
    customerName,
    reload,
    createDestination,
    disableDestination,
  };
}
