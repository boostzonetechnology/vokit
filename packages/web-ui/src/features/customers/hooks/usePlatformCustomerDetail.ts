import { useCallback, useEffect, useState } from "react";

import {
  adjustPlatformCustomerMinutes,
  assignPlatformSubscription,
  changePlatformSubscription,
  getPlatformCustomer,
  getPlatformCustomerUsage,
  listAgencyOptions,
  listPlatformPlanVersions,
  setPlatformCustomerStatus,
} from "@/features/customers/services/customer.service";
import {
  mapCustomerError,
  type CustomerRecord,
  type CustomerUsage,
  type PlanVersionOption,
  type SubscriptionChangeResult,
} from "@/features/customers/types";

export function usePlatformCustomerDetail(customerId: string) {
  const [detail, setDetail] = useState<CustomerRecord | null>(null);
  const [usage, setUsage] = useState<CustomerUsage | null>(null);
  const [planVersions, setPlanVersions] = useState<PlanVersionOption[]>([]);
  const [agencyLabel, setAgencyLabel] = useState("—");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [lastChange, setLastChange] = useState<SubscriptionChangeResult | null>(null);

  const loadDetail = useCallback(async (id: string) => {
    if (!id) {
      setDetail(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [customer, usageRes, versions, agencyRows] = await Promise.all([
        getPlatformCustomer(id),
        getPlatformCustomerUsage(id),
        listPlatformPlanVersions(),
        listAgencyOptions(),
      ]);
      setDetail(customer);
      setUsage(
        usageRes ?? {
          remaining_minutes: customer.remaining_minutes,
          lots: [],
        },
      );
      setPlanVersions(versions);
      const agency = agencyRows.find((row) => row.id === customer.agency_id);
      setAgencyLabel(agency?.display_name || customer.agency_id?.slice(0, 8) || "—");
    } catch (cause) {
      setDetail(null);
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
      const updated = await setPlatformCustomerStatus(customerId, {
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
      await assignPlatformSubscription(customerId, plan_version_id);
      setMessage("Plan assigned. Invoice generated for first assign.");
      setLastChange(null);
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
      const result = await changePlatformSubscription(customerId, plan_version_id);
      setLastChange(result);
      if (result.kind === "upgrade" && result.invoice) {
        setMessage(
          `Upgrade queued. Invoice total ${result.invoice.total_minor ?? 0} ${result.invoice.currency || "USD"} — pay to apply.`,
        );
      } else if (result.kind === "downgrade") {
        setMessage("Downgrade scheduled for period end (or applied if no tighter wait).");
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

  async function adjustMinutes(minutes: number, reason: string) {
    beginAction();
    try {
      const snapshot = await adjustPlatformCustomerMinutes(customerId, { minutes, reason });
      setUsage(snapshot);
      setDetail((prev) =>
        prev ? { ...prev, remaining_minutes: snapshot.remaining_minutes } : prev,
      );
      setMessage(`Minutes adjusted by ${minutes}.`);
    } catch (cause) {
      setActionError(mapCustomerError(cause, "Minutes adjustment failed."));
    } finally {
      setBusy(false);
    }
  }

  return {
    detail,
    usage,
    planVersions,
    agencyLabel,
    error,
    message,
    actionError,
    lastChange,
    loading,
    busy,
    setStatus,
    assignPlan,
    changePlan,
    adjustMinutes,
  };
}
