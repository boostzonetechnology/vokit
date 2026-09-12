import { useEffect, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { AgencyOption, CreateCustomerInput, CustomerRecord } from "@/features/customers/types";

export function useCreatePlatformCustomer() {
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingAgencies, setLoadingAgencies] = useState(true);

  useEffect(() => {
    void (async () => {
      setLoadingAgencies(true);
      try {
        const rows = asList<AgencyOption>(await apiGet<unknown>("/api/v1/platform/agencies"));
        setAgencies(rows);
      } catch {
        setAgencies([]);
      } finally {
        setLoadingAgencies(false);
      }
    })();
  }, []);

  async function createCustomer(input: CreateCustomerInput): Promise<CustomerRecord> {
    setBusy(true);
    setError("");
    try {
      const body: Record<string, string> = {
        agency_id: input.agency_id,
        display_name: input.display_name,
        owner_email: input.owner_email,
      };
      if (input.legal_name) body.legal_name = input.legal_name;
      if (input.phone) body.phone = input.phone;
      if (input.country) body.country = input.country;
      if (input.timezone) body.timezone = input.timezone;

      return await apiSend<CustomerRecord>("/api/v1/platform/customers", "POST", body);
    } catch (cause) {
      const message = isApiError(cause) ? cause.message : "Create failed.";
      setError(message);
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return { createCustomer, agencies, loadingAgencies, error, busy, setError };
}
