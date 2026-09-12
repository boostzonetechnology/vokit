import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { AgencyOption, CustomerRecord } from "@/features/customers/types";

export function usePlatformCustomerList(filters: {
  agencyId: string;
  status: string;
  query: string;
}) {
  const [customers, setCustomers] = useState<CustomerRecord[]>([]);
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const reloadList = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.agencyId) params.set("agency_id", filters.agencyId);
      if (filters.status) params.set("status", filters.status);
      if (filters.query.trim()) params.set("q", filters.query.trim());
      const qs = params.toString();
      const path = qs ? `/api/v1/platform/customers?${qs}` : "/api/v1/platform/customers";

      const [customerRows, agencyRows] = await Promise.all([
        asList<CustomerRecord>(await apiGet<unknown>(path)),
        (async () => {
          try {
            return asList<AgencyOption>(await apiGet<unknown>("/api/v1/platform/agencies"));
          } catch {
            return [] as AgencyOption[];
          }
        })(),
      ]);
      setCustomers(customerRows);
      setAgencies(agencyRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load customers.");
    } finally {
      setLoading(false);
    }
  }, [filters.agencyId, filters.status, filters.query]);

  useEffect(() => {
    void reloadList();
  }, [reloadList]);

  const agencyName = useMemo(() => {
    const map = new Map(
      agencies.map((row) => [row.id, row.display_name || row.id.slice(0, 8)]),
    );
    return (id?: string) => (id ? map.get(id) ?? id.slice(0, 8) : "—");
  }, [agencies]);

  return { customers, agencies, agencyName, error, loading, reloadList };
}
