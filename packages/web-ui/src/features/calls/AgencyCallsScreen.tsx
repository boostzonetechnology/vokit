import { useEffect, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyCalls } from "./hooks/useAgencyCalls";

type Tab = "list" | "detail" | "privacy";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "completed" || value === "answered") return "success";
  if (value.includes("fail") || value === "busy") return "danger";
  if (value === "ringing" || value === "in_progress") return "warning";
  return "neutral";
}

export function AgencyCallsScreen() {
  const {
    calls,
    artifacts,
    customers,
    agents,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    customerFilter,
    setCustomerFilter,
    agentFilter,
    setAgentFilter,
    statusFilter,
    setStatusFilter,
    directionFilter,
    setDirectionFilter,
    customerName,
    agentName,
    reload,
    loadArtifacts,
    grantAccess,
  } = useAgencyCalls();

  const [tab, setTab] = useState<Tab>("list");

  useEffect(() => {
    if (selectedId && tab === "detail") {
      void loadArtifacts(selectedId);
    }
  }, [selectedId, tab, loadArtifacts]);

  const statusOptions = useMemo(
    () => [...new Set(calls.map((row) => row.status).filter(Boolean))] as string[],
    [calls],
  );

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "list", label: "Call list" },
    { id: "detail", label: "Detail" },
    { id: "privacy", label: "Privacy" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Calls
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Agency-wide list, detail, privacy · AG5
          </p>
        </div>
        <ActionButton variant="secondary" onClick={() => void reload()}>
          Refresh
        </ActionButton>
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

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((item) => (
          <ActionButton
            key={item.id}
            variant={tab === item.id ? "secondary" : "outline"}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </ActionButton>
        ))}
      </div>

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <FormField
          label="Search"
          name="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Number, edge id…"
        />
        <FormSelect
          label="Customer"
          name="customer"
          value={customerFilter}
          onChange={(event) => setCustomerFilter(event.target.value)}
        >
          <option value="">All customers</option>
          {customers.map((row) => (
            <option key={row.id} value={row.id}>
              {row.display_name || row.id.slice(0, 8)}
            </option>
          ))}
        </FormSelect>
        <FormSelect
          label="Agent"
          name="agent"
          value={agentFilter}
          onChange={(event) => setAgentFilter(event.target.value)}
        >
          <option value="">All agents</option>
          {agents
            .filter((row) => !customerFilter || row.customer_id === customerFilter)
            .map((row) => (
              <option key={row.id} value={row.id}>
                {row.display_name || row.id.slice(0, 8)}
              </option>
            ))}
        </FormSelect>
        <FormSelect
          label="Status"
          name="status"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="">All statuses</option>
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </FormSelect>
        <FormSelect
          label="Direction"
          name="direction"
          value={directionFilter}
          onChange={(event) => setDirectionFilter(event.target.value)}
        >
          <option value="">All</option>
          <option value="inbound">Inbound</option>
          <option value="outbound">Outbound</option>
        </FormSelect>
      </div>

      {tab === "privacy" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Customer privacy
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Agency access to call recordings, transcripts and summaries is subject to each
            customer agreement and platform policy. Artifact access is authorized per call and
            audited; permanent URLs are never issued to the portal.
          </p>
          <ApiNote>
            AG5-003 — enforce server-side authorization on every artifact access request. Do not
            treat UI visibility as a privacy boundary.
          </ApiNote>
        </article>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
              Agency calls ({calls.length})
            </h2>
            {loading ? (
              <p className="m-0 text-body text-text-muted" role="status">
                Loading…
              </p>
            ) : !calls.length ? (
              <p className="m-0 text-body text-text-muted">No calls match these filters.</p>
            ) : (
              <ul className="m-0 grid max-h-[560px] list-none gap-2 overflow-auto p-0">
                {calls.map((row) => (
                  <li key={row.id}>
                    <button
                      type="button"
                      className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                        selectedId === row.id
                          ? "border-border-brand bg-surface-muted"
                          : "border-border-default bg-surface hover:bg-surface-muted"
                      }`}
                      onClick={() => {
                        setSelectedId(row.id);
                        setTab("detail");
                      }}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-text-primary">
                          {row.remote_e164 || row.e164 || row.id.slice(0, 8)}
                        </span>
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "—"}
                        </StatusBadge>
                      </div>
                      <p className="m-0 mt-1 text-sm text-text-muted">
                        {row.direction || "—"} · {customerName(row.customer_id)} ·{" "}
                        {agentName(row.agent_id)}
                        {row.started_at ? ` · ${row.started_at}` : ""}
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">Call detail</h2>
            {!selected ? (
              <p className="m-0 text-body text-text-muted">Select a call to view detail.</p>
            ) : (
              <div className="grid gap-3">
                <dl className="m-0 grid gap-2 text-sm">
                  <div>
                    <dt className="text-text-muted">Call ID</dt>
                    <dd className="m-0 break-all text-text-primary">{selected.id}</dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Direction / status</dt>
                    <dd className="m-0 text-text-primary">
                      {selected.direction || "—"} · {selected.status || "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Numbers</dt>
                    <dd className="m-0 text-text-primary">
                      {selected.e164 || "—"} ↔ {selected.remote_e164 || "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Outcome</dt>
                    <dd className="m-0 text-text-primary">
                      {selected.end_reason || "—"}
                      {selected.duration_seconds != null
                        ? ` · ${selected.duration_seconds}s`
                        : ""}
                      {selected.billed_minutes != null
                        ? ` · ${selected.billed_minutes} billed min`
                        : ""}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Customer / agent</dt>
                    <dd className="m-0 text-text-primary">
                      {customerName(selected.customer_id)} · {agentName(selected.agent_id)}
                    </dd>
                  </div>
                </dl>

                <h3 className="m-0 text-sm font-semibold text-text-primary">
                  Artifacts (recording / transcript / summary)
                </h3>
                {busy && !artifacts.length ? (
                  <p className="m-0 text-body text-text-muted">Loading artifacts…</p>
                ) : !artifacts.length ? (
                  <p className="m-0 text-body text-text-muted">No artifacts available.</p>
                ) : (
                  <ul className="m-0 grid list-none gap-2 p-0">
                    {artifacts.map((row, index) => (
                      <li
                        key={row.id || `${row.kind}-${index}`}
                        className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                      >
                        <div>
                          <p className="m-0 font-medium text-text-primary">
                            {row.kind || "artifact"}
                          </p>
                          <p className="m-0 text-sm text-text-muted">
                            {row.status || "—"}
                            {row.hold ? " · legal hold" : ""}
                          </p>
                        </div>
                        {row.id ? (
                          <ActionButton
                            variant="outline"
                            disabled={busy}
                            onClick={() => void grantAccess(selected.id, row.id!)}
                          >
                            Request access
                          </ActionButton>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}
                <ApiNote>
                  AG5-002 — tools/outcome appear when enabled on the call record and artifacts
                  when ingest completes.
                </ApiNote>
              </div>
            )}
          </article>
        </div>
      )}
    </section>
  );
}
