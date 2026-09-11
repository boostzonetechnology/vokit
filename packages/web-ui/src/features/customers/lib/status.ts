import type { BadgeTone } from "@/components/ui/StatusBadge";

export function customerStatusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "invited" || value === "pending") return "warning";
  if (value === "suspended" || value === "closed") return "danger";
  return "neutral";
}
