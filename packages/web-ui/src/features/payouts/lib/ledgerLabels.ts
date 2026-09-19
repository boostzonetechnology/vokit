import type { BadgeTone } from "@/components/ui/StatusBadge";

const KIND_LABELS: Record<string, string> = {
  commission_earned: "Commission earned",
  hold_released: "Hold released",
  commission_reversal: "Commission reversal",
  manual_credit: "Manual credit",
  manual_debit: "Manual debit",
  payout_reserved: "Payout reserved",
  payout_released: "Payout released",
  payout_paid: "Payout paid",
  wallet_freeze: "Wallet freeze",
};

export function ledgerKindLabel(kind?: string): string {
  if (!kind) return "Entry";
  return KIND_LABELS[kind] ?? kind.replaceAll("_", " ");
}

export function ledgerStateTone(state?: string): BadgeTone {
  const value = (state ?? "").toLowerCase();
  if (value === "available" || value === "paid" || value === "released") return "success";
  if (value === "held" || value === "on_hold" || value === "pending") return "warning";
  if (value === "frozen" || value === "reversed" || value === "rejected") return "danger";
  return "neutral";
}

export function ledgerStateLabel(state?: string): string {
  const value = (state ?? "").toLowerCase();
  if (value === "on_hold" || value === "held") return "On hold";
  if (value === "available") return "Available";
  if (value === "frozen") return "Frozen";
  if (value === "reversed") return "Reversed";
  if (!value) return "—";
  return value.replaceAll("_", " ");
}
