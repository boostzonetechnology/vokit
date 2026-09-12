import { useState } from "react";

import { apiSend, isApiError } from "@/api";
import type { AgencyRecord, CreateAgencyInput } from "@/features/agencies/types";

export function useCreatePlatformAgency() {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function createAgency(input: CreateAgencyInput): Promise<AgencyRecord> {
    setBusy(true);
    setError("");
    try {
      const database: Record<string, string | number> = {
        username: input.database.username,
        password: input.database.password,
      };
      if (input.database.host) database.host = input.database.host;
      if (typeof input.database.port === "number" && !Number.isNaN(input.database.port)) {
        database.port = input.database.port;
      }

      return await apiSend<AgencyRecord>("/api/v1/platform/agencies", "POST", {
        display_name: input.display_name,
        legal_name: input.legal_name,
        owner_email: input.owner_email,
        commission_rate_bps: input.commission_rate_bps,
        currency: input.currency,
        capabilities: input.capabilities,
        database,
      });
    } catch (cause) {
      const message = isApiError(cause) ? cause.message : "Create failed.";
      setError(message);
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return { createAgency, error, busy, setError };
}
