import { useCallback, useEffect, useState } from "react";

import { apiSend } from "@/api";
import {
  assignAgencySubscription,
  changeAgencySubscription,
  getAgencyCustomer,
  getAgencyCustomerUsage,
  listAgencyPlanVersions,
  safeListRows,
  setAgencyCustomerStatus,
} from "@/features/customers/services/customer.service";
import {
  mapCustomerError,
  type CustomerRecord,
  type CustomerResourceBundle,
  type CustomerUsage,
  type PlanVersionOption,
  type SubscriptionChangeResult,
} from "@/features/customers/types";

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
  const [usage, setUsage] = useState<CustomerUsage | null>(null);
  const [planVersions, setPlanVersions] = useState<PlanVersionOption[]>([]);
  const [resources, setResources] = useState<CustomerResourceBundle>(EMPTY_RESOURCES);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [lastChange, setLastChange] = useState<SubscriptionChangeResult | null>(null);
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
      const [
        customer,
        usageRes,
        versions,
        agentRows,
        numberRows,
        callRows,
        knowledgeRows,
        integrationRows,
        invoiceRows,
      ] = await Promise.all([
        getAgencyCustomer(id),
        getAgencyCustomerUsage(id),
        listAgencyPlanVersions(),
        safeListRows<{ id: string; display_name?: string; status?: string; customer_id?: string }>(
          `/api/v1/agency/agents?customer_id=${encodeURIComponent(id)}`,
        ),
        safeListRows<{
          id: string;
          e164?: string;
          status?: string;
          assigned_customer_id?: string;
          customer_id?: string;
        }>("/api/v1/agency/phone-numbers"),
        safeListRows<{
          id: string;
          status?: string;
          billed_minutes?: number;
          started_at?: string | null;
          customer_id?: string;
        }>("/api/v1/agency/calls"),
        safeListRows<{
          id: string;
          title?: string;
          name?: string;
          status?: string;
          customer_id?: string;
        }>("/api/v1/agency/knowledge"),
        safeListRows<{ id: string; provider?: string; status?: string; customer_id?: string }>(
          "/api/v1/agency/integrations",
        ),
        safeListRows<{ id: string; status?: string; total_minor?: number; currency?: string }>(
          `/api/v1/agency/customer-invoices?customer_id=${encodeURIComponent(id)}`,
        ),
      ]);

      setDetail(customer);
      setUsage(
        usageRes ?? {
          remaining_minutes: customer.remaining_minutes,
          lots: [],
        },
      );
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
      setUsage(null);
      setResources(EMPTY_RESOURCES);
      setError(mapCustomerError(cause, "Failed to load customer detail."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDetail(customerId);
  }, [customerId, loadDetail]);

  function beginAction() {
    setBusy(true);
    setMessage("");
    setActionError("");
  }

  async function setStatus(action: string, reason: string) {
    beginAction();
    try {
      const updated = await setAgencyCustomerStatus(customerId, {
        action,
        reason: reason || undefined,
      });
      setDetail(updated);
      setMessage(`Status updated: ${action.replaceAll("_", " ")}`);
    } catch (cause) {
      setActionError(mapCustomerError(cause, "Status update failed."));
    } finally {
      setBusy(false);
    }
  }

  async function assignPlan(plan_version_id: string) {
    beginAction();
    try {
      await assignAgencySubscription(customerId, plan_version_id);
      setLastChange(null);
      setMessage("Plan assigned. Invoice generated for first assign.");
      await loadDetail(customerId);
    } catch (cause) {
      setActionError(mapCustomerError(cause, "Plan assignment failed."));
    } finally {
      setBusy(false);
    }
  }

  async function changePlan(plan_version_id: string) {
    beginAction();
    try {
      const result = await changeAgencySubscription(customerId, plan_version_id);
      setLastChange(result);
      if (result.kind === "upgrade" && result.invoice) {
        setMessage(
          `Upgrade queued. Invoice total ${result.invoice.total_minor ?? 0} ${result.invoice.currency || "USD"}.`,
        );
      } else if (result.kind === "downgrade") {
        setMessage("Downgrade scheduled for period end when extras fit.");
      } else {
        setMessage(`Plan change applied (${result.kind || "ok"}).`);
      }
      await loadDetail(customerId);
    } catch (cause) {
      setActionError(mapCustomerError(cause, "Plan change failed."));
    } finally {
      setBusy(false);
    }
  }

  async function inviteCustomerUser(email: string, role: string) {
    beginAction();
    try {
      await apiSend("/api/v1/agency/team", "POST", {
        email,
        role,
        customer_id: customerId,
      });
      setMessage(`Invite sent to ${email} (${role}).`);
    } catch (cause) {
      setActionError(mapCustomerError(cause, "Invite failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    detail,
    usage,
    planVersions,
    resources,
    error,
    message,
    actionError,
    lastChange,
    loading,
    busy,
    setStatus,
    assignPlan,
    changePlan,
    inviteCustomerUser,
  };
}
