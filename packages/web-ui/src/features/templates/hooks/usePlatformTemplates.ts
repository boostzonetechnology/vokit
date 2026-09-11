import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import type { AgencyOption, TemplateRecord } from "@/features/templates/types";

function asList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    for (const key of ["results", "items"]) {
      if (Array.isArray(record[key])) return record[key] as T[];
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

export type CreateTemplateInput = {
  name: string;
  industry: string;
  use_case: string;
  description: string;
  languages: string;
  visibility: string;
  selected_agency_ids: string[];
  agent_type: string;
  instructions: string;
  voice_provider: string;
  voice_id: string;
  language: string;
  tools: string[];
  fallback_behavior: string;
};

export function usePlatformTemplates() {
  const [templates, setTemplates] = useState<TemplateRecord[]>([]);
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [visibilityFilter, setVisibilityFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [rows, agencyRows] = await Promise.all([
        asList<TemplateRecord>(await apiGet<unknown>("/api/v1/platform/templates")),
        safeGet<AgencyOption>("/api/v1/platform/agencies"),
      ]);
      setTemplates(rows);
      setAgencies(agencyRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load templates.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return templates.filter((row) => {
      if (visibilityFilter && (row.visibility ?? "") !== visibilityFilter) return false;
      if (!q) return true;
      return [row.name, row.industry, row.use_case, row.visibility, row.status, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [templates, query, visibilityFilter]);

  const selected = templates.find((row) => row.id === selectedId) ?? null;

  async function createTemplate(input: CreateTemplateInput) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<TemplateRecord>("/api/v1/platform/templates", "POST", {
        name: input.name,
        industry: input.industry,
        use_case: input.use_case,
        description: input.description,
        languages: input.languages,
        visibility: input.visibility,
        selected_agency_ids: input.selected_agency_ids,
        agent_type: input.agent_type,
        instructions: input.instructions,
        voice_provider: input.voice_provider,
        voice_id: input.voice_id,
        language: input.language,
        tools: input.tools,
        fallback_behavior: input.fallback_behavior,
      });
      setMessage("Template created with version 1.");
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

  return {
    templates: filtered,
    agencies,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    visibilityFilter,
    setVisibilityFilter,
    reload,
    createTemplate,
  };
}
