import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type {
  CallRow,
  CustomerOption,
  IntegrationRow,
  PhoneNumberRow,
  PlatformAgentRow,
} from "@/features/agents/types";

export type AgencyTemplateOption = {
  id: string;
  name?: string;
  industry?: string;
  use_case?: string;
};

export type AgencyAgentDetail = PlatformAgentRow & {
  timezone?: string;
  voice_provider?: string;
  voice_id?: string;
  language?: string;
  greeting?: string;
  fallback_behavior?: string;
  inbound_enabled?: boolean;
  outbound_enabled?: boolean;
  recording_disclosure?: boolean;
  instructions?: string;
  draft_version?: number | null;
  template_id?: string | null;
};

async function safeGet<T>(path: string): Promise<T[]> {
  try {
    return asList<T>(await apiGet<unknown>(path));
  } catch {
    return [];
  }
}

export function useAgencyAgentsDirectory() {
  const [agents, setAgents] = useState<PlatformAgentRow[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [templates, setTemplates] = useState<AgencyTemplateOption[]>([]);
  const [numbers, setNumbers] = useState<PhoneNumberRow[]>([]);
  const [calls, setCalls] = useState<CallRow[]>([]);
  const [integrations, setIntegrations] = useState<IntegrationRow[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<AgencyAgentDetail | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [agentRows, customerRows, templateRows, numberRows, callRows, integrationRows] =
        await Promise.all([
          safeGet<PlatformAgentRow>("/api/v1/agency/agents"),
          safeGet<CustomerOption>("/api/v1/agency/customers"),
          safeGet<AgencyTemplateOption>("/api/v1/agency/templates"),
          safeGet<PhoneNumberRow>("/api/v1/agency/phone-numbers"),
          safeGet<CallRow>("/api/v1/agency/calls"),
          safeGet<IntegrationRow>("/api/v1/agency/integrations"),
        ]);
      setAgents(agentRows);
      setCustomers(customerRows);
      setTemplates(templateRows);
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

  async function loadAgentDetail(agentId: string) {
    try {
      const detail = await apiGet<AgencyAgentDetail>(`/api/v1/agency/agents/${agentId}`);
      setSelectedDetail(detail);
      return detail;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Failed to load agent detail.");
      setSelectedDetail(null);
      return null;
    }
  }

  async function createAgent(input: {
    customer_id: string;
    display_name: string;
    template_id?: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const body: Record<string, string> = {
        customer_id: input.customer_id,
        display_name: input.display_name,
      };
      if (input.template_id) body.template_id = input.template_id;
      await apiSend("/api/v1/agency/agents", "POST", body);
      setMessage(input.template_id ? "Agent created from template." : "Agent draft created.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function configureAgent(agentId: string, patch: Record<string, unknown>) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await apiSend<AgencyAgentDetail>(
        `/api/v1/agency/agents/${agentId}`,
        "PATCH",
        patch,
      );
      setSelectedDetail(updated);
      setMessage("Agent configuration saved.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Configure failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function publishAgent(agentId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/agents/${agentId}/publish`, "POST", {});
      setMessage("Agent published.");
      await reload();
      await loadAgentDetail(agentId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Publish failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function pauseAgent(agentId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/agents/${agentId}/pause`, "POST", {});
      setMessage("Agent paused.");
      await reload();
      await loadAgentDetail(agentId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Pause failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function cloneAgent(agentId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/agents/${agentId}/clone`, "POST", {});
      setMessage("Agent cloned.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Clone failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function startTestSession(agentId: string, query: string) {
    setBusy(true);
    setMessage("");
    try {
      const result = await apiSend<Record<string, unknown>>(
        `/api/v1/agency/agents/${agentId}/test-sessions`,
        "POST",
        { kind: "test", query },
      );
      setMessage(
        `Test session started${result.id ? `: ${String(result.id).slice(0, 8)}` : "."}`,
      );
      return result;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Test session failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    agents,
    customers,
    templates,
    calls,
    integrations,
    selectedDetail,
    customerName,
    numberByAgent,
    error,
    message,
    loading,
    busy,
    reload,
    loadAgentDetail,
    createAgent,
    configureAgent,
    publishAgent,
    pauseAgent,
    cloneAgent,
    startTestSession,
  };
}
