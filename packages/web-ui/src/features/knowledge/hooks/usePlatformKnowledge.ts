import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import type { KnowledgeRecord } from "@/features/knowledge/types";

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

export type CreateKnowledgeInput = {
  title: string;
  body: string;
  kind: string;
};

export function usePlatformKnowledge() {
  const [sources, setSources] = useState<KnowledgeRecord[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [kindFilter, setKindFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = asList<KnowledgeRecord>(
        await apiGet<unknown>("/api/v1/platform/knowledge"),
      );
      setSources(rows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load knowledge.");
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
      if (kindFilter && (row.kind ?? "") !== kindFilter) return false;
      if (!q) return true;
      return [row.title, row.scope, row.kind, row.status, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [sources, query, kindFilter]);

  const selected = sources.find((row) => row.id === selectedId) ?? null;

  async function createSource(input: CreateKnowledgeInput) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<KnowledgeRecord>("/api/v1/platform/knowledge", "POST", {
        title: input.title,
        body: input.body,
        kind: input.kind,
      });
      setMessage(
        created.status
          ? `Knowledge source created (${created.status}).`
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

  return {
    sources: filtered,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    kindFilter,
    setKindFilter,
    reload,
    createSource,
  };
}
