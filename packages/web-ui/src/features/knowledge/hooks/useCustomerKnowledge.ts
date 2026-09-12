import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, isApiError } from "@/api";
import type { KnowledgeRecord } from "@/features/knowledge/types";
import { asList } from "@/features/platform/lib/list";

export function useCustomerKnowledge() {
  const [sources, setSources] = useState<KnowledgeRecord[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = asList<KnowledgeRecord>(await apiGet<unknown>("/api/v1/customer/knowledge"));
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
    if (!q) return sources;
    return sources.filter((row) =>
      [row.title, row.scope, row.status, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [sources, query]);

  const selected = sources.find((row) => row.id === selectedId) ?? null;

  return {
    sources: filtered,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    setMessage,
    loading,
    query,
    setQuery,
    reload,
  };
}
