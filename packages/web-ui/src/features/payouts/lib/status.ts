import type { BadgeTone } from "@/components/ui/StatusBadge";

export function payoutStatusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "paid" || value === "approved" || value === "usable") return "success";
  if (value === "requested" || value === "processing" || value === "pending") return "warning";
  if (value === "rejected" || value === "frozen" || value === "disabled") return "danger";
  return "neutral";
}
