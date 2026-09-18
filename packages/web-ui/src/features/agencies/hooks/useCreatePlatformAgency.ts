import { useState } from "react";

import { mapAgencyError } from "@/features/agencies/lib/mapAgencyError";
import { createAgency as createAgencyRequest } from "@/features/agencies/services/agency.service";
import type { AgencyRecord, CreateAgencyInput } from "@/features/agencies/types";

export function useCreatePlatformAgency() {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function createAgency(input: CreateAgencyInput): Promise<AgencyRecord> {
    setBusy(true);
    setError("");
    try {
      return await createAgencyRequest(input);
    } catch (cause) {
      setError(mapAgencyError(cause, "Create failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return { createAgency, error, busy, setError };
}
