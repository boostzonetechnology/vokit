import { useCallback, useEffect, useState } from "react";

import { apiGet, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { AgencyRecord } from "@/features/agencies/types";

export function usePlatformAgencyList() {
  const [agencies, setAgencies] = useState<AgencyRecord[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

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

  return { agencies, error, loading, reloadList };
}
