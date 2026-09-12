import { useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { DualLineChart, useCallSeries } from "./components/DualLineChart";
import { useDashboardBundle } from "./hooks/useDashboardBundle";
import {
  formatCount,
  formatDuration,
  formatMoneyMinor,
  formatRelativeTime,
  kpiValue,
  periodLabel,
} from "./lib/format";

function agentLabel(agent: { display_name?: string; name?: string; id: string }) {
  return agent.display_name || agent.name || agent.id.slice(0, 8);
}

function outcomeTone(
  status?: string,
): { label: string; tone: "success" | "info" | "warning" | "danger" | "neutral" } {
  const value = (status ?? "").toLowerCase();
  if (value === "completed" || value === "ended") return { label: "Resolved", tone: "info" };
  if (value === "transferred") return { label: "Transferred", tone: "warning" };
  if (value === "failed" || value === "no_answer" || value === "busy") {
    return { label: "Missed", tone: "danger" };
  }
  if (value === "answered" || value === "in_progress" || value === "ringing") {
    return { label: "In progress", tone: "success" };
  }
  return { label: status || "Unknown", tone: "neutral" };
}

export function AgencyDashboard({ onNavigate }: { onNavigate: (href: string) => void }) {
  const [period, setPeriod] = useState("30d");
  const { data, calls, agents, knowledgeCount, error, loading } = useDashboardBundle(
    "agency",
    period,
    "UTC",
  );
  const callSeries = useCallSeries(calls);

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

  const currency = data.currency ?? "USD";
  const customers = Number(kpiValue(data, "customers") ?? 0);
  const activeAgents = Number(kpiValue(data, "active_agents") ?? 0);
  const numbers = Number(kpiValue(data, "numbers") ?? 0);
  const callsCount = Number(kpiValue(data, "calls") ?? calls.length);
  const minutes = Number(kpiValue(data, "minutes") ?? 0);
  const customerMrr = Number(kpiValue(data, "customer_mrr_minor") ?? 0);
  const commissionEarned = Number(kpiValue(data, "commission_earned_minor") ?? 0);
  const held = Number(kpiValue(data, "held_minor") ?? 0);
  const available = Number(kpiValue(data, "available_minor") ?? data.financial?.available_minor ?? 0);
  const pendingPayout = Number(kpiValue(data, "pending_payout_minor") ?? 0);
  const lifetimePaid = Number(kpiValue(data, "lifetime_paid_minor") ?? 0);

  const alerts = data.alerts ?? {};
  const knowledgeReady = knowledgeCount > 0;
  const month = new Date(data.period.end).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  const liveAgents = agents.slice(0, 5);
  const recent = calls.slice(0, 6);
  const checklist = [
    { id: "customer", label: "Create your first customer", done: customers > 0, href: "/customers" },
    { id: "number", label: "Choose a phone number", done: numbers > 0, href: "/numbers" },
    { id: "prompt", label: "Create an agent", done: agents.length > 0, href: "/agents" },
    { id: "knowledge", label: "Add knowledge base", done: knowledgeReady, href: "/knowledge" },
    { id: "call", label: "Place a test call", done: callsCount > 0, href: "/calls" },
  ];
  const next = checklist.find((step) => !step.done) ?? checklist[checklist.length - 1]!;

  const alertItems = [
    {
      id: "kyc",
      label: "KYC status",
      value: String(alerts.kyc_status ?? "—"),
      href: "/kyc",
      tone:
        String(alerts.kyc_status).toLowerCase() === "verified"
          ? ("success" as const)
          : ("warning" as const),
    },
    {
      id: "invoices",
      label: "Open invoices",
      value: formatCount(Number(alerts.open_invoices ?? 0)),
      href: "/invoices",
      tone: Number(alerts.open_invoices ?? 0) > 0 ? ("warning" as const) : ("success" as const),
    },
    {
      id: "agents",
      label: "Agent errors",
      value: formatCount(Number(alerts.agent_errors ?? 0)),
      href: "/agents",
      tone: Number(alerts.agent_errors ?? 0) > 0 ? ("danger" as const) : ("success" as const),
    },
    {
      id: "payouts",
      label: "Payouts requested",
      value: formatCount(Number(alerts.payout_requested ?? 0)),
      href: "/payouts",
      tone: Number(alerts.payout_requested ?? 0) > 0 ? ("info" as const) : ("neutral" as const),
    },
    {
      id: "wallet",
      label: "Low available balance",
      value: alerts.low_available ? "Yes" : "No",
      href: "/wallet",
      tone: alerts.low_available ? ("danger" as const) : ("success" as const),
    },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Agency overview
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Agency workspace • {month} • AG1 dashboard
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="m-0 font-normal" htmlFor="agency-period">
            <span className="sr-only">Date range</span>
            <select
              id="agency-period"
              value={period}
              onChange={(event) => setPeriod(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body text-text-secondary"
              aria-label={periodLabel(period)}
            >
              <option value="today">Today</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="mtd">Month to date</option>
            </select>
          </label>
          <ActionButton variant="secondary" onClick={() => onNavigate("/customers")}>
            Customers
          </ActionButton>
          <ActionButton onClick={() => onNavigate("/agents")}>Create agent</ActionButton>
        </div>
      </div>

      <div className="grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Customers"
            value={formatCount(customers)}
            hint="In this agency"
            accent="brand"
            onClick={() => onNavigate("/customers")}
          />
          <MetricCard
            label="Active agents"
            value={formatCount(activeAgents)}
            hint="Currently active"
            accent="success"
            onClick={() => onNavigate("/agents")}
          />
          <MetricCard
            label="Numbers"
            value={formatCount(numbers)}
            hint="Provisioned numbers"
            accent="muted"
            onClick={() => onNavigate("/numbers")}
          />
          <MetricCard
            label="Calls"
            value={formatCount(callsCount)}
            hint="In selected period"
            accent="brand"
            onClick={() => onNavigate("/calls")}
          />
          <MetricCard
            label="Minutes"
            value={formatCount(minutes)}
            hint="Billed minutes"
            accent="muted"
            onClick={() => onNavigate("/calls")}
          />
          <MetricCard
            label="Customer revenue"
            value={formatMoneyMinor(customerMrr, currency)}
            hint="Paid invoices in period"
            accent="success"
            onClick={() => onNavigate("/invoices")}
          />
          <MetricCard
            label="Commission earned"
            value={formatMoneyMinor(commissionEarned, currency)}
            hint="Earned in period"
            accent="brand"
            onClick={() => onNavigate("/wallet")}
          />
          <MetricCard
            label="Held"
            value={formatMoneyMinor(held, currency)}
            hint="Not yet available"
            accent="warning"
            onClick={() => onNavigate("/wallet")}
          />
          <MetricCard
            label="Available"
            value={formatMoneyMinor(available, currency)}
            hint="Withdrawable balance"
            accent="success"
            onClick={() => onNavigate("/wallet")}
          />
          <MetricCard
            label="Pending payout"
            value={formatMoneyMinor(pendingPayout, currency)}
            hint="Withdrawal in flight"
            accent="warning"
            onClick={() => onNavigate("/payouts")}
          />
          <MetricCard
            label="Lifetime paid"
            value={formatMoneyMinor(lifetimePaid, currency)}
            hint="All-time payouts"
            accent="muted"
            onClick={() => onNavigate("/payouts")}
          />
          <div className="rounded-xl border border-dashed border-border-strong bg-canvas p-4">
            <p className="m-0 text-body-sm text-text-muted">Expected commission MRR</p>
            <p className="mt-2 mb-0 text-body font-semibold text-text-secondary">Not in API yet</p>
            <p className="mt-2 mb-0 text-body-sm text-text-muted">
              AG1-001 expected commission MRR is not returned by GET /agency/dashboard.
            </p>
          </div>
        </div>

        <ApiNote>
          AG1-002: Failed-integration and customer low-balance alerts are not in the dashboard
          payload yet. Shown alerts use KYC, open invoices, agent errors, payout requests, and
          low available wallet.
        </ApiNote>

        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <DualLineChart
            title="Call volume trends"
            series={callSeries}
            emptyLabel="No call volume in this period yet."
            legendA="Connected"
            legendB="Completed"
          />

          <article className="flex flex-col rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <h3 className="m-0 text-section text-text-primary">Alerts</h3>
            <ul className="mt-4 m-0 flex-1 list-none space-y-3 p-0">
              {alertItems.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between gap-3 bg-transparent p-0 text-left"
                    onClick={() => onNavigate(item.href)}
                  >
                    <div className="min-w-0">
                      <p className="m-0 font-semibold text-text-primary">{item.label}</p>
                      <p className="m-0 text-body-sm text-text-muted">{item.value}</p>
                    </div>
                    <StatusBadge tone={item.tone}>{item.value}</StatusBadge>
                  </button>
                </li>
              ))}
            </ul>
          </article>
        </div>

        <ApiNote>
          AG1-003 Should: Dedicated revenue/minutes trend series is not a separate API. Call volume
          chart above is derived from GET /agency/calls for the selected period.
        </ApiNote>

        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h3 className="m-0 text-section text-text-primary">Recent calls</h3>
              <button
                type="button"
                className="bg-transparent p-0 text-body font-semibold text-text-brand"
                onClick={() => onNavigate("/calls")}
              >
                View call log →
              </button>
            </div>
            {recent.length === 0 ? (
              <p className="m-0 py-10 text-center text-body text-text-muted">No recent calls.</p>
            ) : (
              <div className="overflow-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-label uppercase text-text-muted">
                      <th className="border-0 px-2 py-2">Caller</th>
                      <th className="border-0 px-2 py-2">Agent</th>
                      <th className="border-0 px-2 py-2">Duration</th>
                      <th className="border-0 px-2 py-2">Outcome</th>
                      <th className="border-0 px-2 py-2">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent.map((call) => {
                      const tone = outcomeTone(call.status);
                      const agent = agents.find((row) => row.id === call.agent_id);
                      return (
                        <tr key={call.id}>
                          <td className="px-2 py-3 font-medium text-text-primary">
                            {call.remote_e164 || call.e164 || call.id.slice(0, 8)}
                          </td>
                          <td className="px-2 py-3 text-text-secondary">
                            {agent ? agentLabel(agent) : call.agent_id?.slice(0, 8) || "—"}
                          </td>
                          <td className="px-2 py-3 text-text-secondary">
                            {formatDuration(call.duration_seconds, call.billed_minutes)}
                          </td>
                          <td className="px-2 py-3">
                            <StatusBadge tone={tone.tone}>{tone.label}</StatusBadge>
                          </td>
                          <td className="px-2 py-3 text-text-muted">
                            {formatRelativeTime(call.started_at ?? call.ended_at)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </article>

          <article className="flex flex-col rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <h3 className="m-0 text-section text-text-primary">Live assistants</h3>
            <ul className="mt-4 m-0 flex-1 list-none space-y-3 p-0">
              {liveAgents.length === 0 ? (
                <li className="text-body text-text-muted">No agents yet.</li>
              ) : (
                liveAgents.map((agent) => {
                  const live =
                    agent.status === "active" ||
                    agent.status === "published" ||
                    agent.status === "live";
                  return (
                    <li
                      key={agent.id}
                      className="flex items-center justify-between gap-3 border-b border-border-default pb-3 last:border-b-0"
                    >
                      <div className="min-w-0">
                        <p className="m-0 truncate font-semibold text-text-primary">
                          {agentLabel(agent)}
                        </p>
                        <p className="m-0 text-body-sm text-text-muted">
                          {agent.status || "unknown"}
                        </p>
                      </div>
                      <StatusBadge tone={live ? "success" : "warning"}>
                        {live ? "Live" : "Draft"}
                      </StatusBadge>
                    </li>
                  );
                })
              )}
            </ul>
            <button
              type="button"
              className="mt-4 bg-transparent p-0 text-left text-body font-semibold text-text-brand"
              onClick={() => onNavigate("/agents")}
            >
              Manage agents →
            </button>
          </article>
        </div>

        <article className="flex flex-col rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h3 className="m-0 text-section text-text-primary">Setup checklist</h3>
          <ul className="mt-4 m-0 flex-1 list-none space-y-3 p-0 sm:columns-2">
            {checklist.map((step) => (
              <li key={step.id} className="break-inside-avoid">
                <button
                  type="button"
                  className="flex w-full items-center gap-2.5 bg-transparent p-0 text-left text-body text-text-primary"
                  onClick={() => onNavigate(step.href)}
                >
                  <span
                    className={
                      step.done
                        ? "inline-flex size-5 items-center justify-center rounded-full bg-success text-[10px] text-text-inverse"
                        : "inline-flex size-5 rounded-full border-2 border-border-strong"
                    }
                    aria-hidden
                  >
                    {step.done ? "✓" : ""}
                  </span>
                  <span className={step.done ? "text-text-secondary line-through" : ""}>
                    {step.label}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <ActionButton className="mt-4 w-full sm:w-auto" onClick={() => onNavigate(next.href)}>
            Continue setup →
          </ActionButton>
        </article>
      </div>
    </section>
  );
}
