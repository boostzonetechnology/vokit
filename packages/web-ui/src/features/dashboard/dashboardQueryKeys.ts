import type { Portal } from "@/api";

export const dashboardQueryKeys = {
  all: ["dashboard"] as const,
  summary: (
    portal: Portal,
    period: string,
    timezone: string,
    since?: string,
    until?: string,
  ) =>
    [
      ...dashboardQueryKeys.all,
      portal,
      "summary",
      period,
      timezone,
      since ?? "",
      until ?? "",
    ] as const,
  lists: (portal: Portal) => [...dashboardQueryKeys.all, portal, "lists"] as const,
};

/** KPI / summary payload — slightly longer freshness OK. */
export const DASHBOARD_SUMMARY_STALE_MS = 45_000;

/** Side lists (calls/agents/…) — shorter freshness. */
export const DASHBOARD_LISTS_STALE_MS = 20_000;
