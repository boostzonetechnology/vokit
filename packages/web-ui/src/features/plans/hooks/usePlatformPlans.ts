import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList, safeGetList } from "@/features/platform/lib/list";
import type { CustomerOption, PlanRecord, PlanTermsInput, PlanVersion } from "@/features/plans/types";

export function usePlatformPlans() {
  const [plans, setPlans] = useState<PlanRecord[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
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
      const [rows, customerRows] = await Promise.all([
        asList<PlanRecord>(await apiGet<unknown>("/api/v1/platform/plans")),
        safeGetList<CustomerOption>("/api/v1/platform/customers", (path) =>
          apiGet<unknown>(path),
        ),
      ]);
      setPlans(rows);
      setCustomers(customerRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load plans.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return plans.filter((row) => {
      if (statusFilter && (row.status ?? "") !== statusFilter) return false;
      if (!q) return true;
      return [row.name, row.status, row.id].filter(Boolean).join(" ").toLowerCase().includes(q);
    });
  }, [plans, query, statusFilter]);

  const selected = plans.find((row) => row.id === selectedId) ?? null;

  async function createPlan(input: PlanTermsInput & { name: string }) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<PlanRecord>("/api/v1/platform/plans", "POST", {
        name: input.name,
        price_minor: input.price_minor,
        included_minutes: input.included_minutes,
        allow_topups: input.allow_topups,
        topup_minutes: input.topup_minutes,
        topup_price_minor: input.topup_price_minor,
        overage_enabled: input.overage_enabled,
        overage_price_per_minute_minor: input.overage_price_per_minute_minor,
        grace_seconds: input.grace_seconds,
      });
      setMessage("Plan created with version 1.");
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

  async function addVersion(planId: string, input: PlanTermsInput) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend<PlanVersion>(`/api/v1/platform/plans/${planId}/versions`, "POST", {
        price_minor: input.price_minor,
        included_minutes: input.included_minutes,
        allow_topups: input.allow_topups,
        topup_minutes: input.topup_minutes,
        topup_price_minor: input.topup_price_minor,
        overage_enabled: input.overage_enabled,
        overage_price_per_minute_minor: input.overage_price_per_minute_minor,
        grace_seconds: input.grace_seconds,
      });
      setMessage("New plan version created. Existing subscriptions keep prior version.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Version create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function archivePlan(planId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/plans/${planId}/archive`, "POST", {});
      setMessage("Plan archived.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Archive failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function assignToCustomer(customerId: string, planVersionId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/customers/${customerId}/subscription`, "POST", {
        plan_version_id: planVersionId,
      });
      setMessage("Plan version assigned to customer (invoice generated).");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Assignment failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    plans: filtered,
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
    statusFilter,
    setStatusFilter,
    reload,
    createPlan,
    addVersion,
    archivePlan,
    assignToCustomer,
  };
}
