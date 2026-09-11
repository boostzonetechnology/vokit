import { FormEvent, useMemo, useState, type ReactNode } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { usePlatformAgentsDirectory } from "./hooks/usePlatformAgentsDirectory";
import type { PlatformAgentRow } from "./types";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "paused" || value === "draft" || value === "testing") return "warning";
  if (value === "suspended" || value === "error" || value === "archived") return "danger";
  return "neutral";
}

function ApiGap({ children }: { children: ReactNode }) {
  return (
    <p className="m-0 rounded-lg border border-dashed border-border-strong bg-canvas px-3 py-2 text-body-sm text-text-muted">
      {children}
    </p>
  );
}

type Tab = "manage" | "diagnostics" | "override";

export function PlatformAgentsScreen() {
  const {
    agents,
    customers,
    calls,
    integrations,
    agencyName,
    customerName,
    numberByAgent,
    error,
    message,
    loading,
    busy,
    createAgent,
    publishAgent,
  } = usePlatformAgentsDirectory();

  const [query, setQuery] = useState("");
  const [agencyFilter, setAgencyFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [tab, setTab] = useState<Tab>("manage");
  const [showCreate, setShowCreate] = useState(false);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return agents.filter((row) => {
      if (agencyFilter && row.agency_id !== agencyFilter) return false;
      if (statusFilter && (row.status ?? "").toLowerCase() !== statusFilter) return false;
      if (!q) return true;
      const hay = [
        row.display_name,
        row.agent_type,
        row.status,
        row.id,
        row.agency_id,
        row.customer_id,
        numberByAgent.get(row.id),
        agencyName(row.agency_id),
        customerName(row.customer_id),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [agents, agencyFilter, statusFilter, query, numberByAgent, agencyName, customerName]);

  const selected = agents.find((row) => row.id === selectedId) ?? null;
  const agencyOptions = useMemo(() => {
    const ids = [...new Set(agents.map((row) => row.agency_id).filter(Boolean))] as string[];
    return ids.map((id) => ({ id, label: agencyName(id) }));
  }, [agents, agencyName]);

  const statusOptions = useMemo(() => {
    return [...new Set(agents.map((row) => (row.status ?? "").toLowerCase()).filter(Boolean))];
  }, [agents]);

  const agentCalls = useMemo(() => {
    if (!selected) return [];
    return calls.filter((row) => row.agent_id === selected.id).slice(0, 8);
  }, [calls, selected]);

  const agentIntegrations = useMemo(() => {
    if (!selected) return [];
    return integrations
      .filter(
        (row) =>
          row.customer_id === selected.customer_id || row.agency_id === selected.agency_id,
      )
      .slice(0, 8);
  }, [integrations, selected]);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createAgent({
        customer_id: String(form.get("customer_id") || ""),
        display_name: String(form.get("display_name") || ""),
      });
      setShowCreate(false);
      event.currentTarget.reset();
    } catch {
      /* message set in hook */
    }
  }

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Agents
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Global directory across tenants · SA5-001–004 · Permission: agents.review
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close form" : "Create agent"}
          </ActionButton>
        </div>
      </div>

      {error ? (
        <p className="mb-4 text-danger" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="mb-4 text-body text-text-brand" role="status">
          {message}
        </p>
      ) : null}

      {showCreate ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 text-section text-text-primary">Create agent draft</h2>
          <p className="mt-1 mb-4 text-body-sm text-text-muted">
            Uses <code>POST /api/v1/platform/agents</code>
          </p>
          <form
            className="grid gap-3 sm:grid-cols-[1.2fr_1fr_auto] sm:items-end"
            onSubmit={(event) => void onCreate(event)}
          >
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Customer</span>
              <select
                name="customer_id"
                required
                defaultValue=""
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="" disabled>
                  Select customer
                </option>
                {customers.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.display_name || row.id.slice(0, 8)} ({agencyName(row.agency_id)})
                  </option>
                ))}
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Display name</span>
              <input
                name="display_name"
                required
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <ActionButton type="submit" disabled={busy}>
              Create draft
            </ActionButton>
          </form>
        </article>
      ) : null}

      <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <div className="mb-4 grid gap-3 lg:grid-cols-[1.4fr_1fr_1fr]">
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Search</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Name, type, agency, number…"
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Agency</span>
            <select
              value={agencyFilter}
              onChange={(event) => setAgencyFilter(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">All agencies</option>
              {agencyOptions.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.label}
                </option>
              ))}
            </select>
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Status</span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">All statuses</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>
        </div>

        <h2 className="m-0 mb-3 text-section text-text-primary">
          Global agent directory
          <span className="ml-2 text-body font-normal text-text-muted">
            ({filtered.length})
          </span>
        </h2>

        {loading ? (
          <p className="m-0 text-body text-text-muted">Loading agents…</p>
        ) : filtered.length === 0 ? (
          <p className="m-0 py-10 text-center text-body text-text-muted">No agents found.</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Agent</th>
                  <th className="border-0 px-2 py-2 text-left">Agency</th>
                  <th className="border-0 px-2 py-2 text-left">Customer</th>
                  <th className="border-0 px-2 py-2 text-left">Status</th>
                  <th className="border-0 px-2 py-2 text-left">Type</th>
                  <th className="border-0 px-2 py-2 text-left">Number</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr
                    key={row.id}
                    className={
                      selectedId === row.id
                        ? "bg-brand-subtle/40 cursor-pointer"
                        : "cursor-pointer hover:bg-canvas"
                    }
                    onClick={() => {
                      setSelectedId(row.id);
                      setTab("manage");
                    }}
                  >
                    <td className="px-2 py-3">
                      <p className="m-0 font-semibold text-text-primary">
                        {row.display_name || row.id.slice(0, 8)}
                      </p>
                      <p className="m-0 text-body-sm text-text-muted">{row.id.slice(0, 8)}</p>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{agencyName(row.agency_id)}</td>
                    <td className="px-2 py-3 text-text-secondary">
                      {customerName(row.customer_id)}
                    </td>
                    <td className="px-2 py-3">
                      <StatusBadge tone={statusTone(row.status)}>
                        {row.status || "unknown"}
                      </StatusBadge>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{row.agent_type || "—"}</td>
                    <td className="px-2 py-3 text-text-secondary">
                      {numberByAgent.get(row.id) || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="mt-3 mb-0 text-body-sm text-text-muted">
          Number column is joined client-side from{" "}
          <code>GET /platform/phone-numbers</code> via <code>assigned_agent_id</code>. Agent
          list itself does not include number.
        </p>
      </article>

      {selected ? (
        <AgentDetailPanel
          agent={selected}
          tab={tab}
          onTabChange={setTab}
          busy={busy}
          agencyLabel={agencyName(selected.agency_id)}
          customerLabel={customerName(selected.customer_id)}
          number={numberByAgent.get(selected.id) || "—"}
          calls={agentCalls}
          integrations={agentIntegrations}
          onPublish={() => void publishAgent(selected.id)}
          onClose={() => setSelectedId("")}
        />
      ) : (
        <p className="text-body text-text-muted">Select an agent to manage, diagnose, or override.</p>
      )}
    </section>
  );
}

function AgentDetailPanel({
  agent,
  tab,
  onTabChange,
  busy,
  agencyLabel,
  customerLabel,
  number,
  calls,
  integrations,
  onPublish,
  onClose,
}: {
  agent: PlatformAgentRow;
  tab: Tab;
  onTabChange: (tab: Tab) => void;
  busy: boolean;
  agencyLabel: string;
  customerLabel: string;
  number: string;
  calls: Array<{
    id: string;
    status?: string;
    direction?: string;
    billed_minutes?: number;
    started_at?: string | null;
    remote_e164?: string;
  }>;
  integrations: Array<{ id: string; provider?: string; status?: string }>;
  onPublish: () => void;
  onClose: () => void;
}) {
  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "manage", label: "Create / manage" },
    { id: "diagnostics", label: "Diagnostics" },
    { id: "override", label: "Override" },
  ];

  return (
    <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="m-0 text-section text-text-primary">
            {agent.display_name || agent.id.slice(0, 8)}
          </h2>
          <p className="mt-1 mb-0 text-body text-text-muted">
            {agencyLabel} · {customerLabel} · {number}
          </p>
        </div>
        <ActionButton variant="secondary" onClick={onClose}>
          Close
        </ActionButton>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            className={
              tab === item.id
                ? "rounded-xl bg-brand px-3.5 py-2 text-body font-semibold text-text-inverse"
                : "rounded-xl border border-border-default bg-canvas px-3.5 py-2 text-body font-semibold text-text-secondary"
            }
            onClick={() => onTabChange(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === "manage" ? (
        <div className="grid gap-4">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <InfoTile label="Status" value={agent.status || "—"} />
            <InfoTile label="Type" value={agent.agent_type || "—"} />
            <InfoTile
              label="Published version"
              value={
                agent.published_version == null ? "—" : String(agent.published_version)
              }
            />
            <InfoTile
              label="Production routable"
              value={agent.production_routable ? "Yes" : "No"}
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <ActionButton onClick={onPublish} disabled={busy}>
              Publish
            </ActionButton>
            <ActionButton variant="secondary" disabled title="API not available yet">
              Edit
            </ActionButton>
            <ActionButton variant="secondary" disabled title="API not available yet">
              Pause
            </ActionButton>
            <ActionButton variant="secondary" disabled title="API not available yet">
              Clone
            </ActionButton>
            <ActionButton variant="outline" disabled title="API not available yet">
              Archive
            </ActionButton>
          </div>

          <ApiGap>
            Edit requires PATCH /api/v1/platform/agents/{"{id}"} — abhi API nahi hai (sirf agency
            route hai).
          </ApiGap>
          <ApiGap>
            Pause requires POST /api/v1/platform/agents/{"{id}"}/pause — abhi API nahi hai.
          </ApiGap>
          <ApiGap>
            Clone requires POST /api/v1/platform/agents/{"{id}"}/clone — abhi API nahi hai.
          </ApiGap>
          <ApiGap>
            Archive requires POST /api/v1/platform/agents/{"{id}"}/archive — abhi API nahi hai.
          </ApiGap>
          <p className="m-0 text-body-sm text-text-muted">
            Working now: create (`POST /platform/agents`) and publish (`POST
            /platform/agents/{"{id}"}/publish`). Role: `agents.review`.
          </p>
        </div>
      ) : null}

      {tab === "diagnostics" ? (
        <div className="grid gap-4">
          <ApiGap>
            Runtime configuration diagnostics API nahi hai — platform pe
            `/resolved-instructions` aur `/routing` expose nahi (agency-only).
          </ApiGap>
          <ApiGap>
            Agent error feed API nahi hai — errors / failure stream unavailable.
          </ApiGap>

          <div>
            <h3 className="m-0 mb-2 text-section text-text-primary">Recent calls</h3>
            <p className="mt-0 mb-3 text-body-sm text-text-muted">
              Joined from <code>GET /platform/calls</code> where <code>agent_id</code> matches.
            </p>
            {calls.length === 0 ? (
              <p className="m-0 text-body text-text-muted">No recent calls for this agent.</p>
            ) : (
              <div className="overflow-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-label uppercase text-text-muted">
                      <th className="border-0 px-2 py-2 text-left">Call</th>
                      <th className="border-0 px-2 py-2 text-left">Direction</th>
                      <th className="border-0 px-2 py-2 text-left">Status</th>
                      <th className="border-0 px-2 py-2 text-left">Minutes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {calls.map((call) => (
                      <tr key={call.id}>
                        <td className="px-2 py-3 text-text-primary">
                          {call.remote_e164 || call.id.slice(0, 8)}
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {call.direction || "—"}
                        </td>
                        <td className="px-2 py-3">
                          <StatusBadge tone={statusTone(call.status)}>
                            {call.status || "unknown"}
                          </StatusBadge>
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {call.billed_minutes ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div>
            <h3 className="m-0 mb-2 text-section text-text-primary">Integrations</h3>
            <p className="mt-0 mb-3 text-body-sm text-text-muted">
              Approximate from <code>GET /platform/integrations</code> by customer/agency — not
              agent-scoped diagnostics.
            </p>
            {integrations.length === 0 ? (
              <p className="m-0 text-body text-text-muted">No related integrations found.</p>
            ) : (
              <ul className="m-0 list-none space-y-2 p-0">
                {integrations.map((row) => (
                  <li
                    key={row.id}
                    className="flex items-center justify-between gap-3 rounded-xl border border-border-default px-3 py-2.5"
                  >
                    <span className="font-semibold text-text-primary">
                      {row.provider || row.id.slice(0, 8)}
                    </span>
                    <StatusBadge tone={statusTone(row.status)}>
                      {row.status || "unknown"}
                    </StatusBadge>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}

      {tab === "override" ? (
        <div className="grid gap-4">
          <p className="m-0 text-body text-text-secondary">
            SA5-004: Super Admin can disable an agent immediately for abuse, billing, or
            operational reasons.
          </p>
          <ActionButton variant="outline" disabled title="API not available yet">
            Disable agent now
          </ActionButton>
          <ApiGap>
            Override/disable API nahi hai — e.g. POST /api/v1/platform/agents/{"{id}"}/disable
            (ya suspend) abhi backend mein missing. Chargeback flow alag hai; manual Super Admin
            override route nahi.
          </ApiGap>
        </div>
      ) : null}
    </article>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border-default bg-canvas px-3 py-3">
      <p className="m-0 text-body-sm text-text-muted">{label}</p>
      <p className="mt-1 mb-0 font-semibold text-text-primary">{value}</p>
    </div>
  );
}
