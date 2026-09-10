export function formatCount(value: string | number | boolean): string {
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "number") {
    return new Intl.NumberFormat("en-US").format(value);
  }
  if (/^-?\d+$/.test(value)) {
    return new Intl.NumberFormat("en-US").format(Number(value));
  }
  return value;
}

export function formatMoneyMinor(minor: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(minor / 100);
}

export function formatDuration(seconds?: number, billedMinutes?: number): string {
  if (typeof seconds === "number" && seconds > 0) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${String(secs).padStart(2, "0")}`;
  }
  if (typeof billedMinutes === "number") {
    return `${billedMinutes}:00`;
  }
  return "—";
}

export function formatRelativeTime(iso?: string | null): string {
  if (!iso) {
    return "—";
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  const diffMs = Date.now() - date.getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) {
    return "Just now";
  }
  if (mins < 60) {
    return `${mins}m ago`;
  }
  const hours = Math.round(mins / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function periodLabel(period: string): string {
  switch (period) {
    case "today":
      return "Today";
    case "7d":
      return "Last 7 days";
    case "30d":
      return "Last 30 days";
    case "mtd":
      return "Month to date";
    default:
      return "Custom range";
  }
}

export function kpiValue(
  data: { kpis: Array<{ key: string; value: string | number | boolean }>; currency?: string },
  key: string,
): string | number | boolean | undefined {
  return data.kpis.find((item) => item.key === key)?.value;
}
