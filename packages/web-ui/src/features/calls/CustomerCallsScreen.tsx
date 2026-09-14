import { useEffect, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useCustomerCalls } from "./hooks/useCustomerCalls";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "completed" || value === "answered") return "success";
  if (value.includes("fail") || value === "busy") return "danger";
  if (value === "ringing" || value === "in_progress") return "warning";
  return "neutral";
}

export function CustomerCallsScreen() {
  const {
    calls,
    artifacts,
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
    agentFilter,
    setAgentFilter,
    directionFilter,
    setDirectionFilter,
    statusFilter,
    setStatusFilter,
    numberFilter,
    setNumberFilter,
    agentName,
    reload,
    loadArtifacts,
    grantAccess,
    exportCsv,
  } = useCustomerCalls();

  const [tab, setTab] = useState<"list" | "detail">("list");

  useEffect(() => {
    if (selectedId && tab === "detail") void loadArtifacts(selectedId);
  }, [selectedId, tab, loadArtifacts]);

  const statusOptions = useMemo(
    () => [...new Set(calls.map((row) => row.status).filter(Boolean))] as string[],
    [calls],
  );

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Calls
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Customer call history & artifacts · CU3
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => exportCsv()}>
            Export CSV
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

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <FormField
          label="Search"
          name="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <FormSelect
          label="Agent"
          name="agent"
          value={agentFilter}
          onChange={(event) => setAgentFilter(event.target.value)}
        >
          <option value="">All agents</option>
          {agents.map((row) => (
            <option key={row.id} value={row.id}>
              {row.display_name || row.id.slice(0, 8)}
            </option>
          ))}
        </FormSelect>
        <FormField
          label="Number"
          name="number"
          value={numberFilter}
          onChange={(event) => setNumberFilter(event.target.value)}
          placeholder="E.164"
        />
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
        <FormSelect
          label="Outcome / status"
          name="status"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="">All</option>
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </FormSelect>
      </div>

      <ApiNote>
        CU3-003 / CU3-004 — filters are client-side until query params ship; export is CSV when
        permitted in UI.
      </ApiNote>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Calls ({calls.length})
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading…</p>
          ) : !calls.length ? (
            <p className="m-0 text-body text-text-muted">No calls match these filters.</p>
          ) : (
            <ul className="m-0 grid max-h-[560px] list-none gap-2 overflow-auto p-0">
              {calls.map((row) => (
                <li key={row.id}>
                  <button
                    type="button"
                    className={`w-full rounded-lg border px-3 py-2 text-left ${
                      selectedId === row.id
                        ? "border-border-brand bg-surface-muted"
                        : "border-border-default"
                    }`}
                    onClick={() => {
                      setSelectedId(row.id);
                      setTab("detail");
                    }}
                  >
                    <div className="flex justify-between gap-2">
                      <span className="font-medium text-text-primary">
                        {row.remote_e164 || row.e164 || row.id.slice(0, 8)}
                      </span>
                      <StatusBadge tone={statusTone(row.status)}>
                        {row.status || "—"}
                      </StatusBadge>
                    </div>
                    <p className="m-0 mt-1 text-sm text-text-muted">
                      {row.direction || "—"} · {agentName(row.agent_id)}
                      {row.started_at ? ` · ${row.started_at}` : ""}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Call detail
          </h2>
          {!selected ? (
            <p className="m-0 text-body text-text-muted">Select a call.</p>
          ) : (
            <div className="grid gap-3 text-sm">
              <p className="m-0 text-text-muted">
                {selected.direction} · {selected.end_reason || "—"} ·{" "}
                {selected.duration_seconds != null ? `${selected.duration_seconds}s` : "—"}
              </p>
              <h3 className="m-0 text-sm font-semibold text-text-primary">Artifacts</h3>
              {!artifacts.length ? (
                <p className="m-0 text-body text-text-muted">
                  {busy ? "Loading…" : "No recording/transcript/summary yet."}
                </p>
              ) : (
                <ul className="m-0 grid list-none gap-2 p-0">
                  {artifacts.map((row, index) => (
                    <li
                      key={row.id || `${row.kind}-${index}`}
                      className="flex items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                    >
                      <span>
                        {row.kind || "artifact"} · {row.status || "—"}
                      </span>
                      {row.id ? (
                        <ActionButton
                          variant="outline"
                          disabled={busy}
                          onClick={() => void grantAccess(selected.id, row.id!)}
                        >
                          Access
                        </ActionButton>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
              <ApiNote>CU3-002 — artifacts only when enabled and authorized.</ApiNote>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
