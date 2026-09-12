import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList, safeGetList } from "@/features/platform/lib/list";
import type { AgencyOption, KycCase, KycSettings } from "@/features/kyc/types";

export function usePlatformKyc() {
  const [cases, setCases] = useState<KycCase[]>([]);
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [settings, setSettings] = useState<KycSettings | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [agencyFilter, setAgencyFilter] = useState("");
  const [frozenOnly, setFrozenOnly] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      const qs = params.toString();
      const [rows, agencyRows, settingsRow] = await Promise.all([
        asList<KycCase>(
          await apiGet<unknown>(`/api/v1/platform/kyc/cases${qs ? `?${qs}` : ""}`),
        ),
        safeGetList<AgencyOption>("/api/v1/platform/agencies", (path) => apiGet(path)),
        apiGet<KycSettings>("/api/v1/platform/kyc/settings").catch(() => null),
      ]);
      setCases(rows);
      setAgencies(agencyRows);
      setSettings(settingsRow);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load KYC cases.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return cases.filter((row) => {
      if (agencyFilter && row.agency_id !== agencyFilter) return false;
      if (frozenOnly && !row.frozen) return false;
      if (!q) return true;
      return [row.id, row.agency_id, row.status, row.reason_code, row.inquiry_id, row.session_id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [cases, query, agencyFilter, frozenOnly]);

  const selected = cases.find((row) => row.id === selectedId) ?? null;

  const agencyName = useCallback(
    (agencyId?: string) => {
      if (!agencyId) return "—";
      const match = agencies.find((row) => row.id === agencyId);
      return match?.display_name || agencyId.slice(0, 8);
    },
    [agencies],
  );

  async function overrideCase(input: {
    caseId: string;
    action: string;
    status?: string;
    internal_note: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const payload: Record<string, unknown> = {
        action: input.action,
        internal_note: input.internal_note,
      };
      if (input.status) payload.status = input.status;
      const updated = await apiSend<KycCase>(
        `/api/v1/platform/kyc/cases/${input.caseId}/override`,
        "POST",
        payload,
      );
      setMessage(`KYC override applied (${input.action}).`);
      await reload();
      if (updated.id) setSelectedId(updated.id);
      return updated;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Override failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function saveSettings(input: {
    provider_slug: string;
    api_key_ref: string;
    webhook_secret_ref: string;
    hosted_base_url: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const saved = await apiSend<KycSettings>("/api/v1/platform/kyc/settings", "POST", input);
      setSettings(saved);
      setMessage("KYC provider settings saved (secret refs only).");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Settings save failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    cases: filtered,
    agencies,
    settings,
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
    agencyFilter,
    setAgencyFilter,
    frozenOnly,
    setFrozenOnly,
    agencyName,
    reload,
    overrideCase,
    saveSettings,
  };
}
