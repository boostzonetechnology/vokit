import { useEffect, useState } from "react";

import {
  createPlatformCustomer,
  listAgencyOptions,
} from "@/features/customers/services/customer.service";
import {
  mapCustomerError,
  type AgencyOption,
  type CreateCustomerInput,
  type CustomerRecord,
} from "@/features/customers/types";

export function useCreatePlatformCustomer() {
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingAgencies, setLoadingAgencies] = useState(true);

  useEffect(() => {
    void (async () => {
      setLoadingAgencies(true);
      try {
        setAgencies(await listAgencyOptions());
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
      const body: CreateCustomerInput = {
        agency_id: input.agency_id,
        display_name: input.display_name,
        owner_email: input.owner_email,
      };
      if (input.legal_name) body.legal_name = input.legal_name;
      if (input.phone) body.phone = input.phone;
      if (input.country) body.country = input.country;
      if (input.timezone) body.timezone = input.timezone;
      return await createPlatformCustomer(body);
    } catch (cause) {
      setError(mapCustomerError(cause, "Create failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return { createCustomer, agencies, loadingAgencies, error, busy, setError };
}
