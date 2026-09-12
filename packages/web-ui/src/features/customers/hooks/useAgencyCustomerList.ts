import { useEffect, useMemo, useState } from "react";

import { apiGet, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { CustomerRecord } from "@/features/customers/types";

export function useAgencyCustomerList(filters: { status?: string; query?: string }) {
  const [customers, setCustomers] = useState<CustomerRecord[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    apiGet<unknown>("/api/v1/agency/customers")
      .then((payload) => {
        if (!active) return;
        setCustomers(asList<CustomerRecord>(payload));
        setError("");
      })
      .catch((cause) => {
        if (!active) return;
        setCustomers([]);
        setError(isApiError(cause) ? cause.message : "Failed to load customers.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const filtered = useMemo(() => {
    const status = (filters.status || "").trim().toLowerCase();
    const q = (filters.query || "").trim().toLowerCase();
    return customers.filter((row) => {
      if (status && (row.status || "").toLowerCase() !== status) return false;
      if (!q) return true;
      const hay = [row.display_name, row.legal_name, row.owner_email, row.id, row.status]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [customers, filters.status, filters.query]);

  return { customers: filtered, error, loading };
}
