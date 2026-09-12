import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { KnowledgeRecord } from "@/features/knowledge/types";

export type CustomerOption = {
  id: string;
  display_name?: string;
};

export type AgentOption = {
  id: string;
  display_name?: string;
  customer_id?: string;
  status?: string;
};

export type CreateKnowledgeInput = {
  title: string;
  body: string;
  kind: string;
  scope: "agency" | "customer";
  owner_id?: string;
};

export function useAgencyKnowledge() {
  const [sources, setSources] = useState<KnowledgeRecord[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [scopeFilter, setScopeFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [sourceRows, customerRows, agentRows] = await Promise.all([
        apiGet<unknown>("/api/v1/agency/knowledge").then((data) =>
          asList<KnowledgeRecord>(data),
        ),
        apiGet<unknown>("/api/v1/agency/customers")
          .then((data) => asList<CustomerOption>(data))
          .catch(() => [] as CustomerOption[]),
        apiGet<unknown>("/api/v1/agency/agents")
          .then((data) => asList<AgentOption>(data))
          .catch(() => [] as AgentOption[]),
      ]);
      setSources(sourceRows);
      setCustomers(customerRows);
      setAgents(agentRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load knowledge sources.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return sources.filter((row) => {
      if (scopeFilter && (row.scope ?? "") !== scopeFilter) return false;
      if (!q) return true;
      return [row.title, row.scope, row.kind, row.status, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [sources, query, scopeFilter]);

  const selected = sources.find((row) => row.id === selectedId) ?? null;

  async function createSource(input: CreateKnowledgeInput) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<KnowledgeRecord>("/api/v1/agency/knowledge", "POST", {
        title: input.title,
        body: input.body,
        kind: input.kind,
        scope: input.scope,
        owner_id: input.owner_id || undefined,
      });
      setMessage(
        created.status
          ? `Source created (${created.status}).`
          : "Knowledge source created.",
      );
      await reload();
      if (created.id) setSelectedId(created.id);
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function attachToAgent(agentId: string, sourceId: string, asGlobal = false) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/agents/${agentId}/knowledge`, "POST", {
        source_id: sourceId,
        global: asGlobal,
      });
      setMessage("Source attached to agent.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Attach failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    sources: filtered,
    customers,
    agents,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    scopeFilter,
    setScopeFilter,
    reload,
    createSource,
    attachToAgent,
  };
}
