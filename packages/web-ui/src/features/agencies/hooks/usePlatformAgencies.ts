import { useCallback, useEffect, useState } from "react";

import { apiGet, apiSend, getDashboard, isApiError } from "../../../api";
import type {
  AgencyCapabilities,
  AgencyDashboardSlice,
  AgencyRecord,
  WalletBuckets,
} from "../types";
import { defaultCapabilities } from "../types";

function asList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    for (const key of ["results", "items", "cases"]) {
      if (Array.isArray(record[key])) return record[key] as T[];
    }
  }
  return [];
}

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

export function usePlatformAgencies() {
  const [agencies, setAgencies] = useState<AgencyRecord[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [detail, setDetail] = useState<AgencyRecord | null>(null);
  const [wallet, setWallet] = useState<WalletBuckets | null>(null);
  const [dashboard, setDashboard] = useState<AgencyDashboardSlice | null>(null);
  const [payouts, setPayouts] = useState<Record<string, unknown>[]>([]);
  const [customers, setCustomers] = useState<Record<string, unknown>[]>([]);
  const [agents, setAgents] = useState<Record<string, unknown>[]>([]);
  const [numbers, setNumbers] = useState<Record<string, unknown>[]>([]);
  const [calls, setCalls] = useState<Record<string, unknown>[]>([]);
  const [integrations, setIntegrations] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reloadList = useCallback(async () => {
    setLoading(true);
    try {
      const rows = asList<AgencyRecord>(await apiGet<unknown>("/api/v1/platform/agencies"));
      setAgencies(rows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load agencies.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reloadList();
  }, [reloadList]);

  const loadDetail = useCallback(async (agencyId: string) => {
    if (!agencyId) {
      setDetail(null);
      setWallet(null);
      setDashboard(null);
      setPayouts([]);
      setCustomers([]);
      setAgents([]);
      setNumbers([]);
      setCalls([]);
      setIntegrations([]);
      return;
    }
    try {
      const agency = await apiGet<AgencyRecord>(`/api/v1/platform/agencies/${agencyId}`);
      setDetail(agency);

      const [walletRes, dash, payoutRows, customerRows, agentRows, numberRows, callRows, integrationRows] =
        await Promise.all([
          apiGet<{ buckets?: WalletBuckets }>(`/api/v1/platform/agencies/${agencyId}/wallet`).catch(
            () => null,
          ),
          getDashboard("platform", {
            period: "30d",
            timezone: "UTC",
            agencyId,
          }).catch(() => null),
          safeGet<Record<string, unknown>>("/api/v1/platform/payouts"),
          safeGet<Record<string, unknown>>("/api/v1/platform/customers"),
          safeGet<Record<string, unknown>>("/api/v1/platform/agents"),
          safeGet<Record<string, unknown>>("/api/v1/platform/phone-numbers"),
          safeGet<Record<string, unknown>>("/api/v1/platform/calls"),
          safeGet<Record<string, unknown>>("/api/v1/platform/integrations"),
        ]);

      setWallet(walletRes?.buckets ?? null);
      setDashboard(dash);
      setPayouts(payoutRows.filter((row) => rowAgencyId(row) === agencyId));
      setCustomers(customerRows.filter((row) => rowAgencyId(row) === agencyId));
      setAgents(agentRows.filter((row) => rowAgencyId(row) === agencyId));
      setNumbers(numberRows.filter((row) => rowAgencyId(row) === agencyId));
      setCalls(callRows.filter((row) => rowAgencyId(row) === agencyId));
      setIntegrations(integrationRows.filter((row) => rowAgencyId(row) === agencyId));
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Failed to load agency detail.");
    }
  }, []);

  useEffect(() => {
    void loadDetail(selectedId);
  }, [selectedId, loadDetail]);

  async function createAgency(input: {
    display_name: string;
    legal_name: string;
    owner_email: string;
    commission_rate_bps: number;
    currency: string;
    capabilities: AgencyCapabilities;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<AgencyRecord>("/api/v1/platform/agencies", "POST", {
        display_name: input.display_name,
        legal_name: input.legal_name,
        owner_email: input.owner_email,
        commission_rate_bps: input.commission_rate_bps,
        currency: input.currency,
        capabilities: input.capabilities,
      });
      const invite = created.owner_invitation_token
        ? ` Owner invitation token issued (lab): ${created.owner_invitation_token}`
        : "";
      setMessage(`Agency created.${invite}`);
      await reloadList();
      if (created.id) setSelectedId(created.id);
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function saveProfile(input: { display_name: string; legal_name: string }) {
    if (!selectedId) return;
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<AgencyRecord>(
        `/api/v1/platform/agencies/${selectedId}`,
        "PATCH",
        input,
      );
      setDetail(updated);
      setMessage("Agency profile updated.");
      await reloadList();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Profile update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function setCommission(commission_rate_bps: number) {
    if (!selectedId) return;
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<AgencyRecord>(
        `/api/v1/platform/agencies/${selectedId}/commission`,
        "POST",
        { commission_rate_bps },
      );
      setDetail(updated);
      setMessage("Commission rate updated. Historical ledger entries keep their original snapshot.");
      await reloadList();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Commission update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function setStatus(action: string) {
    if (!selectedId) return;
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<AgencyRecord>(
        `/api/v1/platform/agencies/${selectedId}/status`,
        "POST",
        { action },
      );
      setDetail(updated);
      setMessage(`Status action applied: ${action}`);
      await reloadList();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Status update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function setCapabilities(capabilities: AgencyCapabilities) {
    if (!selectedId) return;
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<AgencyRecord>(
        `/api/v1/platform/agencies/${selectedId}/capabilities`,
        "POST",
        { capabilities },
      );
      setDetail(updated);
      setMessage("Capabilities updated.");
      await reloadList();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Capabilities update failed.");
    } finally {
      setBusy(false);
    }
  }

  return {
    agencies,
    selectedId,
    setSelectedId,
    detail,
    wallet,
    dashboard,
    payouts,
    customers,
    agents,
    numbers,
    calls,
    integrations,
    error,
    message,
    loading,
    busy,
    reloadList,
    createAgency,
    saveProfile,
    setCommission,
    setStatus,
    setCapabilities,
    defaultCapabilities,
  };
}
