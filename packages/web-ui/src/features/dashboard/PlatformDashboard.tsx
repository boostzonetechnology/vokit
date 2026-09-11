import { useMemo, useState } from "react";

import { ActionButton } from "../../components/ui/ActionButton";
import { MetricCard, type MetricAccent } from "../../components/ui/MetricCard";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { DualLineChart, useInvoiceSeries } from "./components/DualLineChart";
import { useDashboardBundle } from "./hooks/useDashboardBundle";
import {
  formatCount,
  formatMoneyMinor,
  formatRelativeTime,
  kpiValue,
  periodLabel,
} from "./lib/format";

const MONEY_KEYS = new Set([
  "mrr_minor",
  "payments_minor",
  "commission_liability_minor",
]);

const KPI_ACCENT: Record<string, MetricAccent> = {
  agencies: "brand",
  active_agencies: "success",
  customers: "brand",
  agents: "muted",
  numbers: "muted",
  calls: "info",
  minutes: "info",
  mrr_minor: "brand",
  payments_minor: "success",
  commission_liability_minor: "warning",
  pending_payouts: "warning",
  kyc_queue: "warning",
};

function toModuleHref(href: string): string {
  const path = href.startsWith("/") ? href.slice(1) : href;
  return `#/${path}`;
}

function toDateInputValue(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toISOString().slice(0, 10);
}

function dayStartIso(date: string): string {
  return `${date}T00:00:00`;
}

function dayEndIso(date: string): string {
  return `${date}T23:59:59`;
}

export function PlatformDashboard({ onNavigate }: { onNavigate: (href: string) => void }) {
  const [period, setPeriod] = useState("30d");
  const [customSince, setCustomSince] = useState("");
  const [customUntil, setCustomUntil] = useState("");
  const range =
    period === "custom" && customSince && customUntil
      ? { since: dayStartIso(customSince), until: dayEndIso(customUntil) }
      : undefined;

  const { data, agents, agencies, invoices, payouts, kycCases, calls, error, loading } =
    useDashboardBundle("platform", period, "UTC", range);

  const revenueSeries = useInvoiceSeries(invoices);
  const agencyName = useMemo(() => {
    const map = new Map(agencies.map((row) => [row.id, row.display_name || row.id.slice(0, 8)]));
    return (id?: string) => (id ? map.get(id) ?? id.slice(0, 8) : "—");
  }, [agencies]);

  const activeAgents = useMemo(
    () =>
      agents.filter((row) => {
        const status = (row.status ?? "").toLowerCase();
        return status === "active" || status === "published" || status === "live";
      }).length,
    [agents],
  );

  const activity = useMemo(() => {
    const rows: Array<{
      id: string;
      event: string;
      agency: string;
      amount: string;
      status: string;
      tone: "success" | "warning" | "info" | "danger" | "neutral";
      time?: string | null;
    }> = [];

    for (const invoice of invoices.slice(0, 8)) {
      rows.push({
        id: `inv-${invoice.id}`,
        event: "Customer payment captured",
        agency: "—",
        amount:
          typeof invoice.total_minor === "number"
            ? formatMoneyMinor(invoice.total_minor, invoice.currency ?? data?.currency)
            : "—",
        status: invoice.status === "paid" ? "Settled" : invoice.status || "Open",
        tone: invoice.status === "paid" ? "success" : "warning",
        time: invoice.paid_at ?? invoice.created_at,
      });
    }
    for (const payout of payouts.slice(0, 4)) {
      rows.push({
        id: `po-${payout.id}`,
        event: "Payout released",
        agency: agencyName(payout.tenant_id),
        amount:
          typeof payout.amount_minor === "number"
            ? formatMoneyMinor(payout.amount_minor, data?.currency)
            : "—",
        status: payout.status === "paid" ? "Paid" : payout.status || "Pending",
        tone: payout.status === "paid" ? "info" : "warning",
        time: payout.created_at,
      });
    }
    for (const kyc of kycCases.slice(0, 4)) {
      rows.push({
        id: `kyc-${kyc.id}`,
        event: "KYC submitted",
        agency: agencyName(kyc.tenant_id),
        amount: "—",
        status: kyc.status || "Pending",
        tone: "warning",
        time: kyc.updated_at,
      });
    }
    return rows
      .sort((a, b) => String(b.time ?? "").localeCompare(String(a.time ?? "")))
      .slice(0, 6);
  }, [invoices, payouts, kycCases, agencyName, data?.currency]);

  const attention = useMemo(() => {
    return kycCases.slice(0, 4).map((row) => ({
      id: row.id,
      name: agencyName(row.tenant_id),
      detail: `KYC status: ${row.status || "pending"}`,
      badge: "KYC due" as const,
      tone: "danger" as const,
    }));
  }, [kycCases, agencyName]);

  if (loading && !data) {
    return <p className="text-body text-text-muted">Loading dashboard…</p>;
  }
  if (error && !data) {
    return (
      <p className="text-danger" role="alert">
        {error}
      </p>
    );
  }
  if (!data) {
    return (
      <p className="text-body text-text-muted">
        {period === "custom" && (!customSince || !customUntil)
          ? "Select a custom start and end date."
          : "No dashboard data."}
      </p>
    );
  }

  const currency = data.currency ?? "USD";
  const financial = data.financial ?? {};
  const gross = Number(financial.gross_revenue_minor ?? kpiValue(data, "mrr_minor") ?? 0);
  const platformShare = Number(financial.estimated_platform_share_minor ?? 0);
  const agencyCommission = Number(financial.agency_commission_minor ?? 0);
  const held = Number(financial.held_minor ?? 0);
  const available = Number(financial.available_minor ?? 0);
  const paidPayouts = Number(financial.paid_payouts_minor ?? 0);
  const pendingPayouts = Number(kpiValue(data, "pending_payouts") ?? 0);
  const kycQueue = Number(kpiValue(data, "kyc_queue") ?? kycCases.length);
  const failed = Number(data.failed_calls ?? 0);
  const callCount = Number(kpiValue(data, "calls") ?? calls.length);
  const failedPct = callCount > 0 ? ((failed / callCount) * 100).toFixed(1) : "0.0";
  const dayLabel = new Date(data.period.end).toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const stats = [
    ...data.kpis.map((card) => {
      const isMoney = MONEY_KEYS.has(card.key);
      return {
        key: card.key,
        label: card.label,
        value: isMoney
          ? formatMoneyMinor(Number(card.value), currency)
          : formatCount(card.value),
        hint:
          card.key === "mrr_minor"
            ? "Period revenue (not recurring MRR)"
            : "From dashboard API",
        accent: KPI_ACCENT[card.key] ?? ("muted" as MetricAccent),
        href: toModuleHref(card.href),
      };
    }),
    {
      key: "active_agents_derived",
      label: "Active agents",
      value: formatCount(activeAgents),
      hint: "Derived from agents list (not dashboard KPI)",
      accent: "success" as MetricAccent,
      href: "#/agents",
    },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Today
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            All agencies • {dayLabel} • Updated just now
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="m-0 font-normal" htmlFor="platform-period">
            <span className="sr-only">Date range</span>
            <select
              id="platform-period"
              value={period}
              onChange={(event) => {
                const next = event.target.value;
                setPeriod(next);
                if (next === "custom" && !customSince && data.period.start) {
                  setCustomSince(toDateInputValue(data.period.start));
                  setCustomUntil(toDateInputValue(data.period.end));
                }
              }}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body text-text-secondary"
              aria-label={periodLabel(period)}
            >
              <option value="today">Today</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="mtd">Month to date</option>
              <option value="custom">Custom range</option>
            </select>
          </label>
          {period === "custom" ? (
            <>
              <label className="m-0 font-normal" htmlFor="platform-since">
                <span className="sr-only">From</span>
                <input
                  id="platform-since"
                  type="date"
                  value={customSince}
                  onChange={(event) => setCustomSince(event.target.value)}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body text-text-secondary"
                />
              </label>
              <label className="m-0 font-normal" htmlFor="platform-until">
                <span className="sr-only">To</span>
                <input
                  id="platform-until"
                  type="date"
                  value={customUntil}
                  onChange={(event) => setCustomUntil(event.target.value)}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body text-text-secondary"
                />
              </label>
            </>
          ) : null}
          <ActionButton variant="outline" onClick={() => onNavigate("#/invoices")}>
            Export report
          </ActionButton>
          <ActionButton onClick={() => onNavigate("#/agencies")}>Create agency</ActionButton>
        </div>
      </div>

      {error ? (
        <p className="mb-4 text-danger" role="alert">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4">
        <div>
          <h2 className="mb-3 mt-0 text-section text-text-primary">Platform stats</h2>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((card) => (
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
        </div>

        <div>
          <h2 className="mb-3 mt-0 text-section text-text-primary">Financial summary</h2>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <MetricCard
              label="Gross customer revenue"
              value={formatMoneyMinor(gross, currency)}
              hint="Paid invoices in selected period"
              accent="brand"
              onClick={() => onNavigate("#/invoices")}
            />
            <MetricCard
              label="Estimated platform share"
              value={formatMoneyMinor(platformShare, currency)}
              hint="Revenue − agency commissions"
              accent="info"
              onClick={() => onNavigate("#/payments")}
            />
            <MetricCard
              label="Agency commissions"
              value={formatMoneyMinor(agencyCommission, currency)}
              hint="Commission earned this period"
              accent="success"
              onClick={() => onNavigate("#/payouts")}
            />
            <MetricCard
              label="Held commission"
              value={formatMoneyMinor(held, currency)}
              hint="Still in hold window"
              accent="warning"
              onClick={() => onNavigate("#/payouts")}
            />
            <MetricCard
              label="Available commission"
              value={formatMoneyMinor(available, currency)}
              hint="Withdrawable now"
              accent="success"
              onClick={() => onNavigate("#/payouts")}
            />
            <MetricCard
              label="Paid payouts"
              value={formatMoneyMinor(paidPayouts, currency)}
              hint="Lifetime paid (wallet projection)"
              accent="muted"
              onClick={() => onNavigate("#/payouts")}
            />
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <DualLineChart
            title="Revenue performance"
            series={revenueSeries}
            emptyLabel="No paid invoices in this period yet."
            legendA="Gross revenue"
            legendB="Commissionable (est.)"
            yFormatter={(v) => formatMoneyMinor(v, currency)}
          />

          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="m-0 text-section text-text-primary">Operational health</h3>
              <StatusBadge tone={failed > 0 || kycQueue > 0 ? "warning" : "success"}>
                {failed > 0 || kycQueue > 0 ? "Needs review" : "Healthy"}
              </StatusBadge>
            </div>
            <ul className="mt-4 m-0 list-none space-y-4 p-0">
              <li className="flex items-center justify-between gap-3">
                <div>
                  <p className="m-0 text-body font-semibold text-text-primary">Failed calls</p>
                  <p className="m-0 text-body-sm text-text-muted">
                    {failed} ({failedPct}% of period calls)
                  </p>
                </div>
                <ActionButton variant="secondary" onClick={() => onNavigate("#/calls")}>
                  Open
                </ActionButton>
              </li>
              <li className="flex items-center justify-between gap-3">
                <div>
                  <p className="m-0 text-body font-semibold text-text-primary">KYC / queue</p>
                  <p className="m-0 text-body-sm text-text-muted">
                    {kycQueue} pending · {pendingPayouts} payout queues
                  </p>
                </div>
                <ActionButton variant="secondary" onClick={() => onNavigate("#/kyc")}>
                  Review
                </ActionButton>
              </li>
              <li className="flex items-center justify-between gap-3">
                <div>
                  <p className="m-0 text-body font-semibold text-text-primary">Webhook failures</p>
                  <p className="m-0 text-body-sm text-text-muted">Not in dashboard API</p>
                </div>
                <StatusBadge tone="neutral">Unavailable</StatusBadge>
              </li>
              <li className="flex items-center justify-between gap-3">
                <div>
                  <p className="m-0 text-body font-semibold text-text-primary">Integration errors</p>
                  <p className="m-0 text-body-sm text-text-muted">Not in dashboard API</p>
                </div>
                <StatusBadge tone="neutral">Unavailable</StatusBadge>
              </li>
              <li className="flex items-center justify-between gap-3">
                <div>
                  <p className="m-0 text-body font-semibold text-text-primary">Low balances</p>
                  <p className="m-0 text-body-sm text-text-muted">Not in dashboard API</p>
                </div>
                <StatusBadge tone="neutral">Unavailable</StatusBadge>
              </li>
              <li className="flex items-center justify-between gap-3">
                <div>
                  <p className="m-0 text-body font-semibold text-text-primary">
                    Telephony / provider incidents
                  </p>
                  <p className="m-0 text-body-sm text-text-muted">Not in dashboard API</p>
                </div>
                <StatusBadge tone="neutral">Unavailable</StatusBadge>
              </li>
            </ul>
          </article>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h3 className="m-0 text-section text-text-primary">Recent activity</h3>
              <button
                type="button"
                className="bg-transparent p-0 text-body font-semibold text-text-brand"
                onClick={() => onNavigate("#/payments")}
              >
                View payments →
              </button>
            </div>
            {activity.length === 0 ? (
              <p className="m-0 py-10 text-center text-body text-text-muted">No recent activity.</p>
            ) : (
              <div className="overflow-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-label uppercase text-text-muted">
                      <th className="border-0 px-2 py-2">Event</th>
                      <th className="border-0 px-2 py-2">Agency</th>
                      <th className="border-0 px-2 py-2">Amount</th>
                      <th className="border-0 px-2 py-2">Status</th>
                      <th className="border-0 px-2 py-2">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activity.map((row) => (
                      <tr key={row.id}>
                        <td className="px-2 py-3 font-medium text-text-primary">{row.event}</td>
                        <td className="px-2 py-3 text-text-secondary">{row.agency}</td>
                        <td className="px-2 py-3 text-text-secondary">{row.amount}</td>
                        <td className="px-2 py-3">
                          <StatusBadge tone={row.tone}>{row.status}</StatusBadge>
                        </td>
                        <td className="px-2 py-3 text-text-muted">{formatRelativeTime(row.time)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>

          <article className="flex flex-col rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <h3 className="m-0 text-section text-text-primary">Agencies needing attention</h3>
            <ul className="mt-4 m-0 flex-1 list-none space-y-3 p-0">
              {attention.length === 0 ? (
                <li className="text-body text-text-muted">No KYC attention items right now.</li>
              ) : (
                attention.map((row) => (
                  <li
                    key={row.id}
                    className="flex items-start justify-between gap-3 border-b border-border-default pb-3 last:border-b-0"
                  >
                    <div className="min-w-0">
                      <p className="m-0 truncate font-semibold text-text-primary">{row.name}</p>
                      <p className="m-0 text-body-sm text-text-muted">{row.detail}</p>
                    </div>
                    <StatusBadge tone={row.tone}>{row.badge}</StatusBadge>
                  </li>
                ))
              )}
            </ul>
            <div className="mt-4 rounded-lg bg-brand-subtle px-3 py-2.5 text-body-sm text-text-brand">
              Commission hold uses platform payout settings (default 15 days).
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}
