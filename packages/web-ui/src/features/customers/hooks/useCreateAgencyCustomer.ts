import { useState } from "react";

import { apiSend, isApiError } from "@/api";
import type { AgencyCreateCustomerInput, CustomerRecord } from "@/features/customers/types";

export function useCreateAgencyCustomer() {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function createCustomer(input: AgencyCreateCustomerInput): Promise<CustomerRecord> {
    setBusy(true);
    setError("");
    try {
      const body: Record<string, string> = {
        display_name: input.display_name,
        owner_email: input.owner_email,
      };
      if (input.legal_name) body.legal_name = input.legal_name;
      if (input.phone) body.phone = input.phone;
      if (input.country) body.country = input.country;
      if (input.timezone) body.timezone = input.timezone;
      return await apiSend<CustomerRecord>("/api/v1/agency/customers", "POST", body);
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Create customer failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return { createCustomer, error, busy, setError };
}
