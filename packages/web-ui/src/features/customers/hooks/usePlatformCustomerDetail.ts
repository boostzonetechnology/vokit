import { useCallback, useEffect, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type {
  CustomerRecord,
  CustomerUsage,
  PlanVersionOption,
} from "@/features/customers/types";

async function safeGet<T>(path: string): Promise<T[]> {
  try {
    return asList<T>(await apiGet<unknown>(path));
  } catch {
    return [];
  }
}

export function usePlatformCustomerDetail(customerId: string) {
  const [detail, setDetail] = useState<CustomerRecord | null>(null);
  const [usage, setUsage] = useState<CustomerUsage | null>(null);
  const [planVersions, setPlanVersions] = useState<PlanVersionOption[]>([]);
  const [agencyLabel, setAgencyLabel] = useState("—");
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
      const [customer, usageRes, planRows, agencyRows] = await Promise.all([
        apiGet<CustomerRecord>(`/api/v1/platform/customers/${id}`),
        apiGet<CustomerUsage>(`/api/v1/platform/customers/${id}/usage`).catch(() => null),
        safeGet<Record<string, unknown>>("/api/v1/platform/plans"),
        safeGet<{ id: string; display_name?: string }>("/api/v1/platform/agencies"),
      ]);
      setDetail(customer);
      setUsage(
        usageRes ?? {
          remaining_minutes: customer.remaining_minutes,
          lots: [],
        },
      );

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

      const agency = agencyRows.find((row) => row.id === customer.agency_id);
      setAgencyLabel(agency?.display_name || customer.agency_id?.slice(0, 8) || "—");
    } catch (cause) {
      setDetail(null);
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
        `/api/v1/platform/customers/${customerId}/status`,
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
      await apiSend(`/api/v1/platform/customers/${customerId}/subscription`, "POST", {
        plan_version_id,
      });
      setMessage("Plan assigned.");
      await loadDetail(customerId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Plan assignment failed.");
    } finally {
      setBusy(false);
    }
  }

  async function adjustMinutes(minutes: number, reason: string) {
    setBusy(true);
    setMessage("");
    try {
      const snapshot = await apiSend<CustomerUsage>(
        `/api/v1/platform/customers/${customerId}/minutes-adjustment`,
        "POST",
        { minutes, reason },
      );
      setUsage(snapshot);
      setDetail((prev) =>
        prev
          ? { ...prev, remaining_minutes: snapshot.remaining_minutes }
          : prev,
      );
      setMessage(`Minutes adjusted by ${minutes}.`);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Minutes adjustment failed.");
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
    loading,
    busy,
    setStatus,
    assignPlan,
    adjustMinutes,
  };
}
