import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "../../../api";
import type { AgencyOption, CustomerRecord, PlanVersionOption } from "../types";

function asList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    for (const key of ["results", "items", "versions"]) {
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

export function usePlatformCustomers() {
  const [customers, setCustomers] = useState<CustomerRecord[]>([]);
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [planVersions, setPlanVersions] = useState<PlanVersionOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [detail, setDetail] = useState<CustomerRecord | null>(null);
  const [invoices, setInvoices] = useState<Record<string, unknown>[]>([]);
  const [calls, setCalls] = useState<Record<string, unknown>[]>([]);
  const [agents, setAgents] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [agencyFilter, setAgencyFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [query, setQuery] = useState("");

  const reloadList = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (agencyFilter) params.set("agency_id", agencyFilter);
      if (statusFilter) params.set("status", statusFilter);
      const qs = params.toString();
      const path = qs ? `/api/v1/platform/customers?${qs}` : "/api/v1/platform/customers";
      const [customerRows, agencyRows, planRows] = await Promise.all([
        asList<CustomerRecord>(await apiGet<unknown>(path)),
        safeGet<AgencyOption>("/api/v1/platform/agencies"),
        safeGet<Record<string, unknown>>("/api/v1/platform/plans"),
      ]);
      setCustomers(customerRows);
      setAgencies(agencyRows);

      const versions: PlanVersionOption[] = [];
      for (const plan of planRows) {
        const planName = String(plan.name || plan.id || "Plan");
        const planId = String(plan.id || "");
        const nested = asList<Record<string, unknown>>(plan.versions);
        for (const version of nested) {
          versions.push({
            id: String(version.id),
            plan_id: planId,
            plan_name: planName,
            version: Number(version.version ?? 0),
            price_minor: Number(version.price_minor ?? 0),
            included_minutes: Number(version.included_minutes ?? 0),
            currency: String(version.currency || "USD"),
          });
        }
      }
      setPlanVersions(versions);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load customers.");
    } finally {
      setLoading(false);
    }
  }, [agencyFilter, statusFilter]);

  useEffect(() => {
    void reloadList();
  }, [reloadList]);

  const agencyName = useMemo(() => {
    const map = new Map(
      agencies.map((row) => [row.id, row.display_name || row.id.slice(0, 8)]),
    );
    return (id?: string) => (id ? map.get(id) ?? id.slice(0, 8) : "—");
  }, [agencies]);

  const loadDetail = useCallback(async (customerId: string) => {
    if (!customerId) {
      setDetail(null);
      setInvoices([]);
      setCalls([]);
      setAgents([]);
      return;
    }
    try {
      const customer = await apiGet<CustomerRecord>(
        `/api/v1/platform/customers/${customerId}`,
      );
      setDetail(customer);
      const [invoiceRows, callRows, agentRows] = await Promise.all([
        safeGet<Record<string, unknown>>(
          `/api/v1/platform/invoices?customer_id=${encodeURIComponent(customerId)}`,
        ),
        safeGet<Record<string, unknown>>("/api/v1/platform/calls"),
        safeGet<Record<string, unknown>>("/api/v1/platform/agents"),
      ]);
      setInvoices(invoiceRows);
      setCalls(callRows.filter((row) => String(row.customer_id) === customerId));
      setAgents(agentRows.filter((row) => String(row.customer_id) === customerId));
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Failed to load customer detail.");
    }
  }, []);

  useEffect(() => {
    void loadDetail(selectedId);
  }, [selectedId, loadDetail]);

  async function createCustomer(input: {
    agency_id: string;
    display_name: string;
    owner_email: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<CustomerRecord>("/api/v1/platform/customers", "POST", input);
      const invite = created.owner_invitation_token
        ? ` Owner invitation token issued (lab): ${created.owner_invitation_token}`
        : "";
      setMessage(`Customer created.${invite}`);
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

  async function setStatus(action: string) {
    if (!selectedId) return;
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<CustomerRecord>(
        `/api/v1/platform/customers/${selectedId}/status`,
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

  async function assignPlan(plan_version_id: string) {
    if (!selectedId) return;
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/customers/${selectedId}/subscription`, "POST", {
        plan_version_id,
      });
      setMessage("Plan assigned. Subscription invoice created.");
      await loadDetail(selectedId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Plan assignment failed.");
    } finally {
      setBusy(false);
    }
  }

  const openBalanceMinor = useMemo(
    () =>
      invoices
        .filter((row) => String(row.status || "").toLowerCase() === "open")
        .reduce((sum, row) => sum + Number(row.total_minor ?? 0), 0),
    [invoices],
  );

  const filteredCustomers = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return customers;
    return customers.filter((row) =>
      [row.display_name, row.id, row.agency_id, row.status]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [customers, query]);

  return {
    customers: filteredCustomers,
    agencies,
    planVersions,
    selectedId,
    setSelectedId,
    detail,
    invoices,
    calls,
    agents,
    openBalanceMinor,
    agencyName,
    agencyFilter,
    setAgencyFilter,
    statusFilter,
    setStatusFilter,
    query,
    setQuery,
    error,
    message,
    loading,
    busy,
    reloadList,
    createCustomer,
    setStatus,
    assignPlan,
  };
}
