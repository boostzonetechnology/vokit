import { useCallback, useEffect, useState } from "react";

import { mapAgencyError } from "@/features/agencies/lib/mapAgencyError";
import { listAgencies } from "@/features/agencies/services/agency.service";
import type { AgencyRecord } from "@/features/agencies/types";

export function usePlatformAgencyList() {
  const [agencies, setAgencies] = useState<AgencyRecord[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [nameQuery, setNameQuery] = useState("");
  const [debouncedName, setDebouncedName] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedName(nameQuery.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [nameQuery]);

  const reloadList = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await listAgencies({
        status: statusFilter || undefined,
        name: debouncedName || undefined,
      });
      setAgencies(rows);
      setError("");
    } catch (cause) {
      setError(mapAgencyError(cause, "Failed to load agencies."));
    } finally {
      setLoading(false);
    }
  }, [statusFilter, debouncedName]);

  useEffect(() => {
    void reloadList();
  }, [reloadList]);

  return {
    agencies,
    error,
    loading,
    statusFilter,
    nameQuery,
    setStatusFilter,
    setNameQuery,
    reloadList,
  };
}
