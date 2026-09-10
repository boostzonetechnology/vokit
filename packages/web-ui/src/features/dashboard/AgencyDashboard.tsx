import { useState } from "react";

import { ActionButton } from "../../components/ui/ActionButton";
import { MetricCard } from "../../components/ui/MetricCard";
import { StatusBadge } from "../../components/ui/StatusBadge";
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

function outcomeTone(status?: string): { label: string; tone: "success" | "info" | "warning" | "danger" | "neutral" } {
  const value = (status ?? "").toLowerCase();
  if (value === "completed" || value === "ended") return { label: "Resolved", tone: "info" };
  if (value === "transferred") return { label: "Transferred", tone: "warning" };
  if (value === "failed" || value === "no_answer" || value === "busy") return { label: "Missed", tone: "danger" };
  if (value === "answered" || value === "in_progress" || value === "ringing") {
    return { label: "Booked", tone: "success" };
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
  const callsCount = Number(kpiValue(data, "calls") ?? calls.length);
  const minutes = Number(kpiValue(data, "minutes") ?? 0);
  const activeAgents = Number(kpiValue(data, "active_agents") ?? 0);
  const available = Number(kpiValue(data, "available_minor") ?? data.financial?.available_minor ?? 0);
  const numbers = Number(kpiValue(data, "numbers") ?? 0);
  const knowledgeReady = knowledgeCount > 0;
  const month = new Date(data.period.end).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  const liveAgents = agents.slice(0, 5);
  const recent = calls.slice(0, 6);
  const checklist = [
    { id: "number", label: "Choose a phone number", done: numbers > 0, href: "#/numbers" },
    { id: "prompt", label: "Write a clear system prompt", done: agents.length > 0, href: "#/agents" },
    { id: "knowledge", label: "Add your knowledge base", done: knowledgeReady, href: "#/knowledge" },
    { id: "call", label: "Place a test call", done: callsCount > 0, href: "#/calls" },
  ];
  const next = checklist.find((step) => !step.done) ?? checklist[checklist.length - 1]!;

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Agency overview
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Agency workspace • {month} • Updated just now
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
          <ActionButton variant="secondary" onClick={() => onNavigate("#/agents")}>
            Test agent
          </ActionButton>
          <ActionButton onClick={() => onNavigate("#/agents")}>Create agent</ActionButton>
        </div>
      </div>

      <div className="grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Calls handled"
            value={formatCount(callsCount)}
            hint="In selected period"
            accent="brand"
            onClick={() => onNavigate("#/calls")}
          />
          <MetricCard
            label="Minutes used"
            value={formatCount(minutes)}
            hint="Billed minutes"
            accent="success"
            onClick={() => onNavigate("#/calls")}
          />
          <MetricCard
            label="Active agents"
            value={formatCount(activeAgents)}
            hint="Currently active"
            accent="muted"
            onClick={() => onNavigate("#/agents")}
          />
          <MetricCard
            label="Remaining balance"
            value={formatMoneyMinor(available, currency)}
            hint="Available wallet funds"
            accent="warning"
            onClick={() => onNavigate("#/wallet")}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <DualLineChart
            title="Call volume"
            series={callSeries}
            emptyLabel="No call volume in this period yet."
            legendA="Connected"
            legendB="Completed"
          />

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
              onClick={() => onNavigate("#/agents")}
            >
              Manage agents →
            </button>
          </article>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h3 className="m-0 text-section text-text-primary">Recent calls</h3>
              <button
                type="button"
                className="bg-transparent p-0 text-body font-semibold text-text-brand"
                onClick={() => onNavigate("#/calls")}
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
            <h3 className="m-0 text-section text-text-primary">Setup checklist</h3>
            <ul className="mt-4 m-0 flex-1 list-none space-y-3 p-0">
              {checklist.map((step) => (
                <li key={step.id}>
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
            <ActionButton className="mt-4 w-full" onClick={() => onNavigate(next.href)}>
              Continue setup →
            </ActionButton>
          </article>
        </div>
      </div>
    </section>
  );
}
