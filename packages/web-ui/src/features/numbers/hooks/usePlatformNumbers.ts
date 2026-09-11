import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { PhoneNumberRecord, ReconcileResult } from "@/features/numbers/types";

function idempotencyKey(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function usePlatformNumbers() {
  const [numbers, setNumbers] = useState<PhoneNumberRecord[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [countryFilter, setCountryFilter] = useState("");
  const [reconcile, setReconcile] = useState<ReconcileResult | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (countryFilter.trim()) params.set("country", countryFilter.trim());
      const qs = params.toString();
      const rows = asList<PhoneNumberRecord>(
        await apiGet<unknown>(`/api/v1/platform/phone-numbers${qs ? `?${qs}` : ""}`),
      );
      setNumbers(rows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load phone numbers.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, countryFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return numbers;
    return numbers.filter((row) =>
      [row.e164, row.provider, row.status, row.area, row.assigned_agency_id, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [numbers, query]);

  const selected = numbers.find((row) => row.id === selectedId) ?? null;

  async function stockNumber(input: {
    e164: string;
    country: string;
    area: string;
    monthly_cost_minor: number;
    provider: string;
    provider_ref: string;
    capabilities: string[];
  }) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<PhoneNumberRecord>("/api/v1/platform/phone-numbers", "POST", {
        e164: input.e164,
        country: input.country,
        area: input.area,
        monthly_cost_minor: input.monthly_cost_minor,
        provider: input.provider,
        provider_ref: input.provider_ref,
        capabilities: input.capabilities,
      });
      setMessage("Number stocked into platform inventory.");
      await reload();
      if (created.id) setSelectedId(created.id);
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Stock failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function purchaseNumber(e164: string) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<PhoneNumberRecord>(
        "/api/v1/platform/phone-numbers",
        "POST",
        { purchase: true, e164 },
        { "Idempotency-Key": idempotencyKey("number-purchase") },
      );
      setMessage("Number purchased through configured provider.");
      await reload();
      if (created.id) setSelectedId(created.id);
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Purchase failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function releaseNumber(numberId: string, providerRelease: boolean) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/phone-numbers/${numberId}/release`, "POST", {
        confirm: true,
        provider_release: providerRelease,
      });
      setMessage(
        providerRelease
          ? "Number released with provider release requested."
          : "Number released (inventory retention).",
      );
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Release failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function runReconcile() {
    setBusy(true);
    setMessage("");
    try {
      const result = await apiSend<ReconcileResult>(
        "/api/v1/platform/phone-numbers/reconcile",
        "POST",
        {},
      );
      setReconcile(result);
      setMessage("Inventory reconcile completed.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Reconcile failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    numbers: filtered,
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
    countryFilter,
    setCountryFilter,
    reconcile,
    reload,
    stockNumber,
    purchaseNumber,
    releaseNumber,
    runReconcile,
  };
}
