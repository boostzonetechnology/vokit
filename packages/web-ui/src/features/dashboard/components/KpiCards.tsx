import { cn } from "@/lib/utils";
import { formatCount, formatMoneyMinor, kpiValue } from "@/features/dashboard/lib/format";
import type { DashboardPayload } from "@/api";

type Accent = "brand" | "success" | "info" | "warning";

const ACCENT_BAR: Record<Accent, string> = {
  brand: "bg-brand",
  success: "bg-success",
  info: "bg-info",
  warning: "bg-warning",
};

const ACCENT_TEXT: Record<Accent, string> = {
  brand: "text-text-brand",
  success: "text-success",
  info: "text-info",
  warning: "text-warning",
};

function MetricCard({
  label,
  value,
  hint,
  accent,
  onClick,
}: {
  label: string;
  value: string;
  hint: string;
  accent: Accent;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="overflow-hidden rounded-xl border border-border-default bg-surface text-left shadow-subtle"
      aria-label={`${label}: ${value}`}
    >
      <span className={cn("block h-1 w-full", ACCENT_BAR[accent])} aria-hidden />
      <span className="block p-4">
        <span className="block text-body-sm text-text-muted">{label}</span>
        <span className="mt-1 block text-page text-text-primary">{value}</span>
        <span className={cn("mt-2 block text-body-sm", ACCENT_TEXT[accent])}>{hint}</span>
      </span>
    </button>
  );
}

export function KpiCards({
  data,
  onNavigate,
}: {
  data: DashboardPayload;
  onNavigate: (href: string) => void;
}) {
  const currency = data.currency ?? "USD";
  const calls = kpiValue(data, "calls");
  const minutes = kpiValue(data, "minutes");
  const activeAgencies = kpiValue(data, "active_agencies");
  const revenue = kpiValue(data, "mrr_minor");
  const available = data.financial?.available_minor;

  const cards = [
    {
      key: "calls",
      label: "Calls handled",
      value: formatCount(calls ?? 0),
      hint: "In selected period",
      accent: "brand" as const,
      href: "/calls",
    },
    {
      key: "minutes",
      label: "Minutes used",
      value: formatCount(minutes ?? 0),
      hint: "Billed minutes",
      accent: "success" as const,
      href: "/calls",
    },
    {
      key: "active_agencies",
      label: "Active agencies",
      value: formatCount(activeAgencies ?? 0),
      hint: "Currently active",
      accent: "info" as const,
      href: "/agencies",
    },
    {
      key: "balance",
      label: "Available balance",
      value:
        typeof available === "number"
          ? formatMoneyMinor(available, currency)
          : typeof revenue === "number"
            ? formatMoneyMinor(revenue, currency)
            : formatMoneyMinor(0, currency),
      hint:
        typeof revenue === "number"
          ? `Period revenue ${formatMoneyMinor(revenue, currency)}`
          : "Ledger projection",
      accent: "warning" as const,
      href: "/payouts",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <MetricCard
          key={card.key}
          label={card.label}
          value={card.value}
          hint={card.hint}
          accent={card.accent}
          onClick={() => onNavigate(card.href)}
        />
      ))}
    </div>
  );
}
