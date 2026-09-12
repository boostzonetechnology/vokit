import { useCallback, useEffect, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type {
  CustomerRecord,
  CustomerResourceBundle,
  PlanVersionOption,
} from "@/features/customers/types";

async function safeGet<T>(path: string): Promise<T[]> {
  try {
    return asList<T>(await apiGet<unknown>(path));
  } catch {
    return [];
  }
}

const EMPTY_RESOURCES: CustomerResourceBundle = {
  agents: [],
  numbers: [],
  calls: [],
  knowledge: [],
  integrations: [],
  invoices: [],
};

export function useAgencyCustomerDetail(customerId: string) {
  const [detail, setDetail] = useState<CustomerRecord | null>(null);
  const [planVersions, setPlanVersions] = useState<PlanVersionOption[]>([]);
  const [resources, setResources] = useState<CustomerResourceBundle>(EMPTY_RESOURCES);
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
      const [customer, planRows, agentRows, numberRows, callRows, knowledgeRows, integrationRows, invoiceRows] =
        await Promise.all([
          apiGet<CustomerRecord>(`/api/v1/agency/customers/${id}`),
          safeGet<Record<string, unknown>>("/api/v1/agency/plans"),
          safeGet<{ id: string; display_name?: string; status?: string; customer_id?: string }>(
            `/api/v1/agency/agents?customer_id=${encodeURIComponent(id)}`,
          ),
          safeGet<{ id: string; e164?: string; status?: string; assigned_customer_id?: string; customer_id?: string }>(
            "/api/v1/agency/phone-numbers",
          ),
          safeGet<{
            id: string;
            status?: string;
            billed_minutes?: number;
            started_at?: string | null;
            customer_id?: string;
          }>("/api/v1/agency/calls"),
          safeGet<{ id: string; title?: string; name?: string; status?: string; customer_id?: string }>(
            "/api/v1/agency/knowledge",
          ),
          safeGet<{ id: string; provider?: string; status?: string; customer_id?: string }>(
            "/api/v1/agency/integrations",
          ),
          safeGet<{ id: string; status?: string; total_minor?: number; currency?: string }>(
            `/api/v1/agency/customer-invoices?customer_id=${encodeURIComponent(id)}`,
          ),
        ]);

      setDetail(customer);

      const versions: PlanVersionOption[] = [];
      for (const plan of planRows) {
        const planName = String(plan.name || plan.id || "Plan");
        const planId = String(plan.id || "");
        const nested = asList<Record<string, unknown>>(plan.versions, ["versions", "items"]);
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

      setResources({
        agents: agentRows,
        numbers: numberRows.filter(
          (row) => row.customer_id === id || row.assigned_customer_id === id,
        ),
        calls: callRows.filter((row) => row.customer_id === id).slice(0, 20),
        knowledge: knowledgeRows.filter((row) => !row.customer_id || row.customer_id === id),
        integrations: integrationRows.filter((row) => row.customer_id === id),
        invoices: invoiceRows,
      });
    } catch (cause) {
      setDetail(null);
      setResources(EMPTY_RESOURCES);
      setError(isApiError(cause) ? cause.message : "Failed to load customer detail.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDetail(customerId);
  }, [customerId, loadDetail]);

  async function setStatus(action: string, reason: string) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<CustomerRecord>(
        `/api/v1/agency/customers/${customerId}/status`,
        "POST",
        { action, reason },
      );
      setDetail(updated);
      setMessage(`Status updated: ${action}`);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Status update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function assignPlan(plan_version_id: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/customers/${customerId}/subscription`, "POST", {
        plan_version_id,
      });
      setMessage("Plan assigned. Refresh detail after payment settlement if needed.");
      await loadDetail(customerId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Plan assignment failed.");
    } finally {
      setBusy(false);
    }
  }

  async function inviteCustomerUser(email: string, role: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend("/api/v1/agency/team", "POST", {
        email,
        role,
        customer_id: customerId,
      });
      setMessage(`Invite sent to ${email} (${role}).`);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Invite failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    detail,
    planVersions,
    resources,
    error,
    message,
    loading,
    busy,
    setStatus,
    assignPlan,
    inviteCustomerUser,
  };
}
