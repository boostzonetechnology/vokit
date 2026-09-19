import type { BadgeTone } from "@/components/ui/StatusBadge";

export function billingStatusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "paid" || value === "captured" || value === "succeeded") return "success";
  if (value === "open" || value === "pending" || value === "processing") return "warning";
  if (value === "failed" || value === "void" || value === "lost") return "danger";
  return "neutral";
}
