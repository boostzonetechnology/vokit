import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import type {
  AgencyOption,
  CallRow,
  CustomerOption,
  IntegrationRow,
  PhoneNumberRow,
  PlatformAgentRow,
} from "@/features/agents/types";

function asList<T>(data: unknown): T[] {
  if (Array.isArray(data)) {
    return data as T[];
  }
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    for (const key of ["results", "items", "agents", "calls"]) {
      if (Array.isArray(record[key])) {
        return record[key] as T[];
      }
    }
  }
  return [];
}

async function safeGet<T>(path: string): Promise<T[]> {
  try {
    return asList<T>(await apiGet<unknown>(path));
  } catch {
    return [];
  }
}

export function usePlatformAgentsDirectory() {
  const [agents, setAgents] = useState<PlatformAgentRow[]>([]);
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [numbers, setNumbers] = useState<PhoneNumberRow[]>([]);
  const [calls, setCalls] = useState<CallRow[]>([]);
  const [integrations, setIntegrations] = useState<IntegrationRow[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [agentRows, agencyRows, customerRows, numberRows, callRows, integrationRows] =
        await Promise.all([
          safeGet<PlatformAgentRow>("/api/v1/platform/agents"),
          safeGet<AgencyOption>("/api/v1/platform/agencies"),
          safeGet<CustomerOption>("/api/v1/platform/customers"),
          safeGet<PhoneNumberRow>("/api/v1/platform/phone-numbers"),
          safeGet<CallRow>("/api/v1/platform/calls"),
          safeGet<IntegrationRow>("/api/v1/platform/integrations"),
        ]);
      setAgents(agentRows);
      setAgencies(agencyRows);
      setCustomers(customerRows);
      setNumbers(numberRows);
      setCalls(callRows);
      setIntegrations(integrationRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load agents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const agencyName = useMemo(() => {
    const map = new Map(
      agencies.map((row) => [row.id, row.display_name || row.id.slice(0, 8)]),
    );
    return (id?: string) => (id ? map.get(id) ?? id.slice(0, 8) : "—");
  }, [agencies]);

  const customerName = useMemo(() => {
    const map = new Map(
      customers.map((row) => [row.id, row.display_name || row.id.slice(0, 8)]),
    );
    return (id?: string) => (id ? map.get(id) ?? id.slice(0, 8) : "—");
  }, [customers]);

  const numberByAgent = useMemo(() => {
    const map = new Map<string, string>();
    for (const row of numbers) {
      if (row.assigned_agent_id && row.e164) {
        map.set(row.assigned_agent_id, row.e164);
      }
    }
    return map;
  }, [numbers]);

  async function createAgent(input: { customer_id: string; display_name: string }) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend("/api/v1/platform/agents", "POST", input);
      setMessage("Agent draft created.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function publishAgent(agentId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/agents/${agentId}/publish`, "POST", {});
      setMessage("Agent published.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Publish failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    agents,
    agencies,
    customers,
    calls,
    integrations,
    agencyName,
    customerName,
    numberByAgent,
    error,
    message,
    setMessage,
    loading,
    busy,
    reload,
    createAgent,
    publishAgent,
  };
}
