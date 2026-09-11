import type { BadgeTone } from "@/components/ui/StatusBadge";

export function agencyStatusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active" || value === "healthy" || value === "ready") return "success";
  if (value === "invited" || value === "restricted" || value === "pending" || value === "under_review") {
    return "warning";
  }
  if (value === "suspended" || value === "closed" || value === "unhealthy") return "danger";
  return "neutral";
}

export function bpsToPercent(bps?: number): string {
  if (typeof bps !== "number") return "—";
  return `${(bps / 100).toFixed(2)}%`;
}
