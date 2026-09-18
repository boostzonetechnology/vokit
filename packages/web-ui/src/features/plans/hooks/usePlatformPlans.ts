import { useCallback, useEffect, useMemo, useState } from "react";

import { isApiError } from "@/api";
import {
  addPlanVersion,
  archivePlan as archivePlanRequest,
  assignPlanToCustomer,
  createPlan as createPlanRequest,
  listCustomerOptions,
  listPlans,
} from "@/features/plans/services/plan.service";
import type { CustomerOption, PlanRecord, PlanTermsInput } from "@/features/plans/types";

export function usePlatformPlans() {
  const [plans, setPlans] = useState<PlanRecord[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [rows, customerRows] = await Promise.all([listPlans(), listCustomerOptions()]);
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

  function beginAction() {
    setBusy(true);
    setMessage("");
    setActionError("");
  }

  async function createPlan(input: PlanTermsInput & { name: string }) {
    beginAction();
    try {
      const created = await createPlanRequest(input);
      setMessage("Plan created with version 1.");
      await reload();
      if (created.id) setSelectedId(created.id);
      return created;
    } catch (cause) {
      setActionError(isApiError(cause) ? cause.message : "Create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function addVersion(planId: string, input: PlanTermsInput) {
    beginAction();
    try {
      await addPlanVersion(planId, input);
      setMessage("New plan version created. Existing subscriptions keep prior version.");
      await reload();
    } catch (cause) {
      setActionError(isApiError(cause) ? cause.message : "Version create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function archivePlan(planId: string) {
    beginAction();
    try {
      await archivePlanRequest(planId);
      setMessage("Plan archived.");
      await reload();
    } catch (cause) {
      setActionError(isApiError(cause) ? cause.message : "Archive failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function assignToCustomer(customerId: string, planVersionId: string) {
    beginAction();
    try {
      await assignPlanToCustomer(customerId, planVersionId);
      setMessage("Plan version assigned to customer (invoice generated).");
    } catch (cause) {
      setActionError(isApiError(cause) ? cause.message : "Assignment failed.");
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
    actionError,
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
