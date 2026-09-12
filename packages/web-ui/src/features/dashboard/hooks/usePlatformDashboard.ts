import { useEffect, useState } from "react";

import {
  DashboardPayload,
  apiGet,
  getDashboard,
  isApiError,
} from "@/api";

export type PlatformCallRow = {
  id: string;
  agency_id?: string;
  customer_id?: string;
  agent_id?: string;
  remote_e164?: string;
  e164?: string;
  direction?: string;
  status?: string;
  billed_minutes?: number;
  duration_seconds?: number;
  started_at?: string | null;
  ended_at?: string | null;
};

export type PlatformAgentRow = {
  id: string;
  display_name?: string;
  name?: string;
  status?: string;
  customer_id?: string;
};

function asList<T>(data: unknown): T[] {
  if (Array.isArray(data)) {
    return data as T[];
  }
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    for (const key of ["results", "items", "calls", "agents"]) {
      if (Array.isArray(record[key])) {
        return record[key] as T[];
      }
    }
  }
  return [];
}

export function usePlatformDashboard(period: string, timezone: string) {
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [calls, setCalls] = useState<PlatformCallRow[]>([]);
  const [agents, setAgents] = useState<PlatformAgentRow[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([
      getDashboard("platform", { period, timezone }),
      apiGet<unknown>("/api/v1/platform/calls").catch(() => []),
      apiGet<unknown>("/api/v1/platform/agents").catch(() => []),
    ])
      .then(([dashboard, callsPayload, agentsPayload]) => {
        if (!active) {
          return;
        }
        setData(dashboard);
        setCalls(asList<PlatformCallRow>(callsPayload));
        setAgents(asList<PlatformAgentRow>(agentsPayload));
        setError("");
      })
      .catch((cause) => {
        if (active) {
          setError(isApiError(cause) ? cause.message : "Dashboard failed.");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [period, timezone]);

  return { data, calls, agents, error, loading };
}
