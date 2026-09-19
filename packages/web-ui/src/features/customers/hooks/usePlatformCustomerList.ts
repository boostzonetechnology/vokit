import { useCallback, useEffect, useMemo, useState } from "react";

import {
  listAgencyOptions,
  listPlatformCustomers,
} from "@/features/customers/services/customer.service";
import { mapCustomerError, type AgencyOption, type CustomerRecord } from "@/features/customers/types";

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
      const [customerRows, agencyRows] = await Promise.all([
        listPlatformCustomers({
          agencyId: filters.agencyId,
          status: filters.status,
          query: filters.query,
        }),
        listAgencyOptions(),
      ]);
      setCustomers(customerRows);
      setAgencies(agencyRows);
      setError("");
    } catch (cause) {
      setError(mapCustomerError(cause, "Failed to load customers."));
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
