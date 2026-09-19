import { useState } from "react";

import {
  createAgencyCustomer,
} from "@/features/customers/services/customer.service";
import {
  mapCustomerError,
  type AgencyCreateCustomerInput,
  type CustomerRecord,
} from "@/features/customers/types";

export function useCreateAgencyCustomer() {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function createCustomer(input: AgencyCreateCustomerInput): Promise<CustomerRecord> {
    setBusy(true);
    setError("");
    try {
      const body: AgencyCreateCustomerInput = {
        display_name: input.display_name,
        owner_email: input.owner_email,
      };
      if (input.legal_name) body.legal_name = input.legal_name;
      if (input.phone) body.phone = input.phone;
      if (input.country) body.country = input.country;
      if (input.timezone) body.timezone = input.timezone;
      return await createAgencyCustomer(body);
    } catch (cause) {
      setError(mapCustomerError(cause, "Create customer failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return { createCustomer, error, busy, setError };
}
