import { useCallback, useEffect, useState } from "react";

import { apiGet, apiSend, getDashboard, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type {
  AgencyCapabilities,
  AgencyDashboardSlice,
  AgencyNote,
  AgencyRecord,
  WalletBuckets,
} from "@/features/agencies/types";

async function safeGet<T>(path: string): Promise<T[]> {
  try {
    return asList<T>(await apiGet<unknown>(path));
  } catch {
    return [];
  }
}

function rowAgencyId(row: Record<string, unknown>): string {
  return String(row.agency_id ?? row.tenant_id ?? row.assigned_agency_id ?? "");
}

export function usePlatformAgencyDetail(agencyId: string) {
  const [detail, setDetail] = useState<AgencyRecord | null>(null);
  const [wallet, setWallet] = useState<WalletBuckets | null>(null);
  const [dashboard, setDashboard] = useState<AgencyDashboardSlice | null>(null);
  const [payouts, setPayouts] = useState<Record<string, unknown>[]>([]);
  const [customers, setCustomers] = useState<Record<string, unknown>[]>([]);
  const [agents, setAgents] = useState<Record<string, unknown>[]>([]);
  const [numbers, setNumbers] = useState<Record<string, unknown>[]>([]);
  const [calls, setCalls] = useState<Record<string, unknown>[]>([]);
  const [integrations, setIntegrations] = useState<Record<string, unknown>[]>([]);
  const [notes, setNotes] = useState<AgencyNote[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const loadDetail = useCallback(async (id: string) => {
    if (!id) {
      setDetail(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const agency = await apiGet<AgencyRecord>(`/api/v1/platform/agencies/${id}`);
      setDetail(agency);

      const [
        walletRes,
        dash,
        payoutRows,
        customerRows,
        agentRows,
        numberRows,
        callRows,
        integrationRows,
        noteRows,
      ] = await Promise.all([
        apiGet<{ buckets?: WalletBuckets }>(`/api/v1/platform/agencies/${id}/wallet`).catch(
          () => null,
        ),
        getDashboard("platform", {
          period: "30d",
          timezone: "UTC",
          agencyId: id,
        }).catch(() => null),
        safeGet<Record<string, unknown>>("/api/v1/platform/payouts"),
        safeGet<Record<string, unknown>>("/api/v1/platform/customers"),
        safeGet<Record<string, unknown>>("/api/v1/platform/agents"),
        safeGet<Record<string, unknown>>("/api/v1/platform/phone-numbers"),
        safeGet<Record<string, unknown>>("/api/v1/platform/calls"),
        safeGet<Record<string, unknown>>("/api/v1/platform/integrations"),
        safeGet<AgencyNote>(`/api/v1/platform/agencies/${id}/notes`),
      ]);

      setWallet(walletRes?.buckets ?? null);
      setDashboard(dash);
      setPayouts(payoutRows.filter((row) => rowAgencyId(row) === id));
      setCustomers(customerRows.filter((row) => rowAgencyId(row) === id));
      setAgents(agentRows.filter((row) => rowAgencyId(row) === id));
      setNumbers(numberRows.filter((row) => rowAgencyId(row) === id));
      setCalls(callRows.filter((row) => rowAgencyId(row) === id));
      setIntegrations(integrationRows.filter((row) => rowAgencyId(row) === id));
      setNotes(noteRows);
    } catch (cause) {
      setDetail(null);
      setError(isApiError(cause) ? cause.message : "Failed to load agency detail.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDetail(agencyId);
  }, [agencyId, loadDetail]);

  async function saveProfile(input: { display_name: string; legal_name: string }) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<AgencyRecord>(
        `/api/v1/platform/agencies/${agencyId}`,
        "PATCH",
        input,
      );
      setDetail(updated);
      setMessage("Agency profile updated.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Profile update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function setCommission(commission_rate_bps: number) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<AgencyRecord>(
        `/api/v1/platform/agencies/${agencyId}/commission`,
        "POST",
        { commission_rate_bps },
      );
      setDetail(updated);
      setMessage("Commission rate updated. Historical ledger entries keep their original snapshot.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Commission update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function setStatus(action: string) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<AgencyRecord>(
        `/api/v1/platform/agencies/${agencyId}/status`,
        "POST",
        { action },
      );
      setDetail(updated);
      setMessage(`Status action applied: ${action}`);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Status update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function setCapabilities(capabilities: AgencyCapabilities) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<AgencyRecord>(
        `/api/v1/platform/agencies/${agencyId}/capabilities`,
        "POST",
        { capabilities },
      );
      setDetail(updated);
      setMessage("Capabilities updated.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Capabilities update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function addNote(input: { body: string; risk_flag: boolean }) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<AgencyNote>(
        `/api/v1/platform/agencies/${agencyId}/notes`,
        "POST",
        input,
      );
      setNotes((prev) => [created, ...prev]);
      setMessage("Internal note added.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Could not add note.");
    } finally {
      setBusy(false);
    }
  }

  return {
    detail,
    wallet,
    dashboard,
    payouts,
    customers,
    agents,
    numbers,
    calls,
    integrations,
    notes,
    error,
    message,
    loading,
    busy,
    saveProfile,
    setCommission,
    setStatus,
    setCapabilities,
    addNote,
  };
}
