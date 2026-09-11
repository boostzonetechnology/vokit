import type { DashboardPayload } from "@/api";
import { periodLabel } from "@/features/dashboard/lib/format";

export function DashboardHeader({
  data,
  period,
  onPeriodChange,
  onNavigate,
}: {
  data: DashboardPayload;
  period: string;
  onPeriodChange: (period: string) => void;
  onNavigate: (href: string) => void;
}) {
  const month = new Date(data.period.end).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  return (
    <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div>
        <h1 className="m-0 text-page text-text-primary">Platform overview</h1>
        <p className="mt-1 mb-0 text-body text-text-muted">
          Platform control • {month} • Updated just now
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <label className="m-0 font-normal" htmlFor="dashboard-period">
          <span className="sr-only">Date range</span>
          <select
            id="dashboard-period"
            value={period}
            onChange={(event) => onPeriodChange(event.target.value)}
            className="rounded-lg border border-border-default bg-surface px-3 py-2 text-body text-text-secondary"
            aria-label={`Date range: ${periodLabel(period)}`}
          >
            <option value="today">Today</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="mtd">Month to date</option>
          </select>
        </label>
        <button
          type="button"
          className="rounded-lg border border-border-default bg-surface px-3 py-2 text-body font-semibold text-text-primary"
          onClick={() => onNavigate("/agents")}
        >
          Test agent
        </button>
        <button
          type="button"
          className="rounded-lg bg-brand px-3 py-2 text-body font-semibold text-text-inverse"
          onClick={() => onNavigate("/agents")}
        >
          Create agent
        </button>
      </div>
    </div>
  );
}
