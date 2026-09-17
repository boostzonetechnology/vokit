import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend } from "@/api";
import { mapAgentError } from "@/features/agents/lib/mapAgentError";
import { asList } from "@/features/platform/lib/list";
import type {
  AgencyAgentDetail,
  AgentKnowledgeAttachment,
  AgentRoutingResult,
  CallRow,
  CustomerOption,
  IntegrationRow,
  PhoneNumberRow,
  PlatformAgentRow,
} from "@/features/agents/types";
import type { KnowledgeRecord } from "@/features/knowledge/types";
import type { TransferDestination } from "@/features/transfers/types";

export type AgencyTemplateOption = {
  id: string;
  name?: string;
  industry?: string;
  use_case?: string;
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
  const [transfers, setTransfers] = useState<TransferDestination[]>([]);
  const [knowledgeSources, setKnowledgeSources] = useState<KnowledgeRecord[]>([]);
  const [attachedKnowledge, setAttachedKnowledge] = useState<AgentKnowledgeAttachment[]>([]);
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);
  const [routing, setRouting] = useState<AgentRoutingResult | null>(null);
  const [routingLoading, setRoutingLoading] = useState(false);
  const [selectedDetail, setSelectedDetail] = useState<AgencyAgentDetail | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [
        agentRows,
        customerRows,
        templateRows,
        numberRows,
        callRows,
        integrationRows,
        transferRows,
        knowledgeRows,
      ] = await Promise.all([
        safeGet<PlatformAgentRow>("/api/v1/agency/agents"),
        safeGet<CustomerOption>("/api/v1/agency/customers"),
        safeGet<AgencyTemplateOption>("/api/v1/agency/templates"),
        safeGet<PhoneNumberRow>("/api/v1/agency/phone-numbers"),
        safeGet<CallRow>("/api/v1/agency/calls"),
        safeGet<IntegrationRow>("/api/v1/agency/integrations"),
        safeGet<TransferDestination>("/api/v1/agency/transfers"),
        safeGet<KnowledgeRecord>("/api/v1/agency/knowledge"),
      ]);
      setAgents(agentRows);
      setCustomers(customerRows);
      setTemplates(templateRows);
      setNumbers(numberRows);
      setCalls(callRows);
      setIntegrations(integrationRows);
      setTransfers(transferRows);
      setKnowledgeSources(knowledgeRows);
      setError("");
    } catch (cause) {
      setError(mapAgentError(cause, "Failed to load agents."));
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

  const loadAgentKnowledge = useCallback(async (agentId: string) => {
    setKnowledgeLoading(true);
    try {
      const rows = await apiGet<unknown>(`/api/v1/agency/agents/${agentId}/knowledge`).then(
        (data) => asList<AgentKnowledgeAttachment>(data),
      );
      setAttachedKnowledge(rows);
    } catch (cause) {
      setAttachedKnowledge([]);
      setMessage(mapAgentError(cause, "Failed to load agent knowledge."));
    } finally {
      setKnowledgeLoading(false);
    }
  }, []);

  const fetchRouting = useCallback(async (agentId: string) => {
    setRoutingLoading(true);
    try {
      const result = await apiGet<AgentRoutingResult>(
        `/api/v1/agency/agents/${agentId}/routing`,
      );
      setRouting(result);
      return result;
    } catch (cause) {
      setRouting(null);
      setMessage(mapAgentError(cause, "Failed to check routing."));
      return null;
    } finally {
      setRoutingLoading(false);
    }
  }, []);

  const loadAgentDetail = useCallback(
    async (agentId: string) => {
      try {
        const detail = await apiGet<AgencyAgentDetail>(`/api/v1/agency/agents/${agentId}`);
        setSelectedDetail(detail);
        setRouting(null);
        void loadAgentKnowledge(agentId);
        return detail;
      } catch (cause) {
        setMessage(mapAgentError(cause, "Failed to load agent detail."));
        setSelectedDetail(null);
        setAttachedKnowledge([]);
        return null;
      }
    },
    [loadAgentKnowledge],
  );

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
      setMessage(mapAgentError(cause, "Create failed."));
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
      setMessage(mapAgentError(cause, "Configure failed."));
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
      await fetchRouting(agentId);
    } catch (cause) {
      setMessage(mapAgentError(cause, "Publish failed."));
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
      setMessage(mapAgentError(cause, "Pause failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function cloneAgent(agentId: string, input?: { customer_id?: string }) {
    setBusy(true);
    setMessage("");
    try {
      const body: Record<string, string> = {};
      if (input?.customer_id) body.customer_id = input.customer_id;
      await apiSend(`/api/v1/agency/agents/${agentId}/clone`, "POST", body);
      setMessage(
        input?.customer_id
          ? "Agent cloned onto the selected customer."
          : "Agent cloned onto the same customer.",
      );
      await reload();
    } catch (cause) {
      setMessage(mapAgentError(cause, "Clone failed."));
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
        `Test session started${result.id ? `: ${String(result.id).slice(0, 8)}` : "."} (text only — not SIP).`,
      );
      return result;
    } catch (cause) {
      setMessage(mapAgentError(cause, "Test session failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function attachKnowledge(agentId: string, sourceId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/agents/${agentId}/knowledge`, "POST", {
        source_id: sourceId,
      });
      setMessage("Knowledge source attached.");
      await loadAgentKnowledge(agentId);
    } catch (cause) {
      setMessage(mapAgentError(cause, "Attach failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function detachKnowledge(agentId: string, sourceId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/agents/${agentId}/knowledge/${sourceId}`, "DELETE", {});
      setMessage("Knowledge source detached.");
      await loadAgentKnowledge(agentId);
    } catch (cause) {
      setMessage(mapAgentError(cause, "Detach failed."));
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
    transfers,
    knowledgeSources,
    attachedKnowledge,
    knowledgeLoading,
    routing,
    routingLoading,
    selectedDetail,
    customerName,
    numberByAgent,
    error,
    message,
    loading,
    busy,
    reload,
    loadAgentDetail,
    loadAgentKnowledge,
    fetchRouting,
    createAgent,
    configureAgent,
    publishAgent,
    pauseAgent,
    cloneAgent,
    startTestSession,
    attachKnowledge,
    detachKnowledge,
  };
}
