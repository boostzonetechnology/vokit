import { useEffect, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformCalls } from "./hooks/usePlatformCalls";

type Tab = "search" | "detail" | "cost" | "export";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "completed" || value === "answered") return "success";
  if (value.includes("fail") || value === "busy") return "danger";
  if (value === "ringing" || value === "in_progress") return "warning";
  return "neutral";
}

export function PlatformCallsScreen() {
  const {
    calls,
    artifacts,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    agencyFilter,
    setAgencyFilter,
    customerFilter,
    setCustomerFilter,
    agentFilter,
    setAgentFilter,
    numberFilter,
    setNumberFilter,
    statusFilter,
    setStatusFilter,
    directionFilter,
    setDirectionFilter,
    reload,
    loadArtifacts,
    grantAccess,
  } = usePlatformCalls();

  const [tab, setTab] = useState<Tab>("search");

  useEffect(() => {
    if (selectedId && tab === "detail") {
      void loadArtifacts(selectedId);
    }
  }, [selectedId, tab, loadArtifacts]);

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "search", label: "Search" },
    { id: "detail", label: "Detail" },
    { id: "cost", label: "Cost" },
    { id: "export", label: "Export" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Call records
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA14-001–004 · Permissions: calls.review, recordings.review
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
          <button
            key={item.id}
            type="button"
            className={
              tab === item.id
                ? "rounded-xl bg-brand px-3.5 py-2 text-body font-semibold text-text-inverse"
                : "rounded-xl border border-border-default bg-canvas px-3.5 py-2 text-body font-semibold text-text-secondary"
            }
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {(tab === "search" || tab === "detail") && (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <FilterField label="Agency id" value={agencyFilter} onChange={setAgencyFilter} />
            <FilterField label="Customer id" value={customerFilter} onChange={setCustomerFilter} />
            <FilterField label="Agent id" value={agentFilter} onChange={setAgentFilter} />
            <FilterField label="Number" value={numberFilter} onChange={setNumberFilter} />
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Status</span>
              <input
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Direction</span>
              <select
                value={directionFilter}
                onChange={(event) => setDirectionFilter(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="">All</option>
                <option value="inbound">inbound</option>
                <option value="outbound">outbound</option>
              </select>
            </label>
          </div>
          <ApiNote>
            Server filters currently support agency_id and customer_id. Agent, number, status, and
            direction are applied client-side. Date-range query params are not exposed on GET
            /api/v1/platform/calls yet.
          </ApiNote>

          <h2 className="mb-3 mt-4 text-section text-text-primary">
            Calls
            <span className="ml-2 text-body font-normal text-text-muted">({calls.length})</span>
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading calls…</p>
          ) : calls.length === 0 ? (
            <p className="m-0 py-8 text-center text-body text-text-muted">No calls found.</p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Call</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">Direction</th>
                    <th className="border-0 px-2 py-2 text-left">Number</th>
                    <th className="border-0 px-2 py-2 text-left">Minutes</th>
                    <th className="border-0 px-2 py-2 text-left">Agency</th>
                  </tr>
                </thead>
                <tbody>
                  {calls.map((row) => (
                    <tr
                      key={row.id}
                      className={
                        selectedId === row.id
                          ? "cursor-pointer bg-brand-subtle/40"
                          : "cursor-pointer hover:bg-canvas"
                      }
                      onClick={() => {
                        setSelectedId(row.id);
                        setTab("detail");
                      }}
                    >
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.id.slice(0, 8)}
                      </td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.direction || "—"}</td>
                      <td className="px-2 py-3 text-text-secondary">{row.e164 || "—"}</td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.billed_minutes ?? "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.agency_id?.slice(0, 8) || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      )}

      {tab === "detail" && selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Call detail</h2>
          <div className="mb-4 grid gap-3 sm:grid-cols-2">
            <InfoTile label="Provider / edge ID" value={selected.edge_call_id || "—"} />
            <InfoTile label="Billable minutes" value={String(selected.billed_minutes ?? "—")} />
            <InfoTile label="Agent" value={selected.agent_id || "—"} />
            <InfoTile label="Customer" value={selected.customer_id || "—"} />
            <InfoTile label="Remote" value={selected.remote_e164 || "—"} />
            <InfoTile label="Voicemail" value={selected.voicemail_status || "—"} />
          </div>
          <h3 className="m-0 mb-2 text-body font-semibold text-text-primary">
            Artifacts (recording / transcript / summary)
          </h3>
          {busy && artifacts.length === 0 ? (
            <p className="m-0 text-body text-text-muted">Loading artifacts…</p>
          ) : artifacts.length === 0 ? (
            <p className="m-0 text-body text-text-muted">No artifacts for this call.</p>
          ) : (
            <div className="grid gap-2">
              {artifacts.map((item) => (
                <div
                  key={item.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border-default bg-canvas px-3 py-3"
                >
                  <div>
                    <p className="m-0 font-semibold text-text-primary">
                      {item.kind || item.id?.slice(0, 8)}
                    </p>
                    <p className="mt-1 mb-0 text-body-sm text-text-muted">
                      {item.status || "—"}
                      {item.hold ? " · on hold" : ""}
                    </p>
                  </div>
                  {item.id ? (
                    <ActionButton
                      variant="outline"
                      disabled={busy}
                      onClick={() => void grantAccess(selected.id, item.id!)}
                    >
                      Grant access
                    </ActionButton>
                  ) : null}
                </div>
              ))}
            </div>
          )}
          <div className="mt-4">
            <ApiNote>
              Platform call index does not yet return started_at, duration_seconds, tool activity, or
              summary text inline. Use artifacts endpoints for recording/transcript access when
              enabled.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "cost" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Cost components</h2>
          <ActionButton disabled title="API not available yet">
            Show provider / AI cost
          </ActionButton>
          <div className="mt-4">
            <ApiNote>
              SA14-003 (Should): provider/AI cost breakdown is not exposed on platform call APIs
              yet.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "export" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Export</h2>
          <ActionButton disabled title="API not available yet">
            Export filtered metadata
          </ActionButton>
          <div className="mt-4">
            <ApiNote>
              SA14-004 (Should): filtered call metadata export endpoint is not available yet.
            </ApiNote>
          </div>
        </article>
      ) : null}
    </section>
  );
}

function FilterField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="m-0 grid gap-1.5 font-normal">
      <span className="text-body-sm text-text-muted">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
      />
    </label>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border-default bg-canvas px-3 py-3">
      <p className="m-0 text-body-sm text-text-muted">{label}</p>
      <p className="mt-1 mb-0 break-all font-semibold text-text-primary">{value}</p>
    </div>
  );
}
