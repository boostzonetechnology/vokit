import { useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { DualLineChart, useCallSeries } from "./components/DualLineChart";
import { useDashboardBundle } from "./hooks/useDashboardBundle";
import {
  formatCount,
  formatMoneyMinor,
  formatRelativeTime,
  kpiValue,
  periodLabel,
} from "./lib/format";

function outcomeTone(
  status?: string,
): { label: string; tone: "success" | "info" | "warning" | "danger" | "neutral" } {
  const value = (status ?? "").toLowerCase();
  if (value === "completed" || value === "ended") return { label: "Completed", tone: "info" };
  if (value === "failed" || value === "no_answer" || value === "busy") {
    return { label: "Missed", tone: "danger" };
  }
  if (value === "answered" || value === "in_progress" || value === "ringing") {
    return { label: "In progress", tone: "success" };
  }
  return { label: status || "Unknown", tone: "neutral" };
}

export function CustomerDashboard({ onNavigate }: { onNavigate: (href: string) => void }) {
  const [period, setPeriod] = useState("30d");
  const { data, invoices, calls, agents, paymentMethods, error, loading } = useDashboardBundle(
    "customer",
    period,
    "UTC",
  );
  const callSeries = useCallSeries(calls);

  const openTotal = useMemo(
    () =>
      invoices
        .filter((row) => (row.status ?? "").toLowerCase() === "open")
        .reduce((sum, row) => sum + Number(row.total_minor ?? row.amount_minor ?? 0), 0),
    [invoices],
  );

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
  if (!data) return null;

  const agentsCount = Number(kpiValue(data, "agents") ?? agents.length);
  const callsCount = Number(kpiValue(data, "calls") ?? calls.length);
  const minutesUsed = Number(kpiValue(data, "minutes_used") ?? 0);
  const minutesRemaining = Number(kpiValue(data, "minutes_remaining") ?? 0);
  const plan = String(kpiValue(data, "plan") ?? "none");
  const openInvoices = Number(kpiValue(data, "open_invoices") ?? 0);
  const alerts = data.alerts ?? {};
  const recent =
    (data.recent_calls as Array<Record<string, string | number>> | undefined)?.slice(0, 6) ??
    calls.slice(0, 6);
  const defaultMethod = paymentMethods.find((row) => row.is_default) ?? paymentMethods[0];

  const serviceAlerts = [
    {
      key: "low_minutes",
      active: Boolean(alerts.low_minutes),
      label: "Low minutes",
      detail: "Usage is running low — consider a top-up.",
      href: "/usage",
      tone: "warning" as const,
    },
    {
      key: "payment_due",
      active: Boolean(alerts.payment_due),
      label: "Payment due",
      detail: "An invoice needs attention.",
      href: "/invoices",
      tone: "danger" as const,
    },
    {
      key: "agent_offline",
      active: Boolean(alerts.agent_offline),
      label: "Agent offline",
      detail: "One or more agents are not routable.",
      href: "/agents",
      tone: "warning" as const,
    },
    {
      key: "unread_notifications",
      active: Boolean(alerts.unread_notifications),
      label: "Notifications",
      detail: `${alerts.unread_notifications || "Unread"} alerts in your inbox.`,
      href: "/notifications",
      tone: "info" as const,
    },
  ].filter((item) => item.active);

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Overview
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Agents, usage, plan & recent calls · CU1 · {periodLabel(period)}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="m-0 font-normal" htmlFor="customer-period">
            <span className="sr-only">Period</span>
            <select
              id="customer-period"
              value={period}
              onChange={(event) => setPeriod(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body text-text-secondary"
            >
              <option value="today">Today</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="mtd">Month to date</option>
            </select>
          </label>
          <ActionButton variant="outline" onClick={() => onNavigate("/usage")}>
            Top up minutes
          </ActionButton>
          <ActionButton onClick={() => onNavigate("/invoices")}>View invoices</ActionButton>
        </div>
      </div>

      <div className="grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <MetricCard
            label="Agents"
            value={formatCount(agentsCount)}
            hint={`${agents.filter((row) => (row.status ?? "").toLowerCase() === "active").length} active`}
            accent="brand"
            onClick={() => onNavigate("/agents")}
          />
          <MetricCard
            label="Calls this period"
            value={formatCount(callsCount)}
            hint="Customer-scoped call volume"
            accent="muted"
            onClick={() => onNavigate("/calls")}
          />
          <MetricCard
            label="Minutes used"
            value={formatCount(minutesUsed)}
            hint={`${formatCount(minutesRemaining)} remaining`}
            accent="success"
            onClick={() => onNavigate("/usage")}
          />
          <MetricCard
            label="Plan"
            value={plan === "none" ? "None" : plan}
            hint={plan === "none" ? "No active subscription" : "Active assignment"}
            accent="muted"
            onClick={() => onNavigate("/invoices")}
          />
          <MetricCard
            label="Invoice status"
            value={openInvoices > 0 ? `${openInvoices} open` : "Up to date"}
            hint={
              openTotal > 0
                ? `${formatMoneyMinor(openTotal, "USD")} outstanding`
                : "No open balance"
            }
            accent={openInvoices > 0 ? "warning" : "success"}
            onClick={() => onNavigate("/invoices")}
          />
          <MetricCard
            label="Payment method"
            value={
              defaultMethod
                ? `${defaultMethod.brand || "Card"} ···${defaultMethod.last4 || "••••"}`
                : "Not on file"
            }
            hint="Processor-hosted methods when available"
            accent="muted"
            onClick={() => onNavigate("/payment-methods")}
          />
        </div>

        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Service alerts</h2>
          {!serviceAlerts.length ? (
            <p className="m-0 text-body text-text-muted">No active service alerts.</p>
          ) : (
            <ul className="m-0 grid list-none gap-2 p-0 sm:grid-cols-2">
              {serviceAlerts.map((alert) => (
                <li key={alert.key}>
                  <button
                    type="button"
                    className="flex w-full items-start justify-between gap-3 rounded-lg border border-border-default px-3 py-3 text-left hover:bg-surface-muted"
                    onClick={() => onNavigate(alert.href)}
                  >
                    <div>
                      <p className="m-0 font-semibold text-text-primary">{alert.label}</p>
                      <p className="m-0 mt-1 text-sm text-text-muted">{alert.detail}</p>
                    </div>
                    <StatusBadge tone={alert.tone}>{alert.label}</StatusBadge>
                  </button>
                </li>
              ))}
            </ul>
          )}
          <ApiNote>CU1-002 — low minutes, payment due, agent offline and unread notices.</ApiNote>
        </article>

        <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
          <DualLineChart
            title="Call activity"
            series={callSeries}
            emptyLabel="No calls in this period yet."
            legendA="Calls"
            legendB="Minutes (est.)"
            yFormatter={(value) => formatCount(value)}
          />
          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <div className="mb-3 flex items-center justify-between gap-2">
              <h3 className="m-0 text-section text-text-primary">Recent calls</h3>
              <button
                type="button"
                className="bg-transparent p-0 text-body font-semibold text-text-brand"
                onClick={() => onNavigate("/calls")}
              >
                View all →
              </button>
            </div>
            {!recent.length ? (
              <p className="m-0 text-body text-text-muted">No recent calls.</p>
            ) : (
              <ul className="m-0 grid list-none gap-2 p-0">
                {recent.map((row) => {
                  const id = String(row.id);
                  const status = String(row.status ?? "");
                  const tone = outcomeTone(status);
                  return (
                    <li
                      key={id}
                      className="flex items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                    >
                      <div>
                        <p className="m-0 font-medium text-text-primary">
                          {String(row.remote_e164 || row.e164 || id.slice(0, 8))}
                        </p>
                        <p className="m-0 text-sm text-text-muted">
                          {String(row.direction || "—")}
                          {row.started_at
                            ? ` · ${formatRelativeTime(String(row.started_at))}`
                            : ""}
                        </p>
                      </div>
                      <StatusBadge tone={tone.tone}>{tone.label}</StatusBadge>
                    </li>
                  );
                })}
              </ul>
            )}
          </article>
        </div>
      </div>
    </section>
  );
}
