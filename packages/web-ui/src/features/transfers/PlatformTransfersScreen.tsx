import { useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformTransfers } from "./hooks/usePlatformTransfers";

type Tab = "directory" | "override" | "diagnostics";

function statusTone(status?: string, disabled?: boolean): BadgeTone {
  if (disabled || (status ?? "").toLowerCase() === "disabled") return "danger";
  if ((status ?? "").toLowerCase() === "active") return "success";
  return "neutral";
}

export function PlatformTransfersScreen() {
  const {
    destinations,
    failedCalls,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    reload,
    disableDestination,
  } = usePlatformTransfers();

  const [tab, setTab] = useState<Tab>("directory");

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "directory", label: "Directory" },
    { id: "override", label: "Override" },
    { id: "diagnostics", label: "Diagnostics" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Transfers
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA10-001–003 · Permission: transfers.review
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

      {tab === "directory" || tab === "override" ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 grid gap-3 lg:grid-cols-2">
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Search</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Label, kind, agency…"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Status</span>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="">All</option>
                <option value="active">Active</option>
                <option value="disabled">Disabled</option>
              </select>
            </label>
          </div>

          <h2 className="m-0 mb-3 text-section text-text-primary">
            Transfer directory
            <span className="ml-2 text-body font-normal text-text-muted">
              ({destinations.length})
            </span>
          </h2>

          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading destinations…</p>
          ) : destinations.length === 0 ? (
            <p className="m-0 py-10 text-center text-body text-text-muted">
              No transfer destinations indexed.
            </p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Label</th>
                    <th className="border-0 px-2 py-2 text-left">Kind</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">Agency</th>
                    <th className="border-0 px-2 py-2 text-left">Customer</th>
                  </tr>
                </thead>
                <tbody>
                  {destinations.map((row) => (
                    <tr
                      key={row.id}
                      className={
                        selectedId === row.id
                          ? "cursor-pointer bg-brand-subtle/40"
                          : "cursor-pointer hover:bg-canvas"
                      }
                      onClick={() => setSelectedId(row.id)}
                    >
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.label || row.id.slice(0, 8)}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.kind || "—"}</td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status, row.platform_disabled)}>
                          {row.platform_disabled ? "platform_disabled" : row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.agency_id?.slice(0, 8) || "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.customer_id?.slice(0, 8) || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      ) : null}

      {tab === "override" && selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 text-section text-text-primary">
            Disable {selected.label || selected.id.slice(0, 8)}
          </h2>
          <p className="mt-1 mb-4 text-body text-text-secondary">
            POST /api/v1/platform/transfers/{"{id}"}/disable with confirm=true.
          </p>
          <ActionButton
            disabled={busy || selected.platform_disabled || selected.status === "disabled"}
            onClick={() => void disableDestination(selected.id)}
          >
            Confirm disable destination
          </ActionButton>
          <div className="mt-4">
            <ApiNote>
              Platform override permanently marks the destination unsafe/invalid for live transfers.
              Re-enable is not exposed on the platform API yet.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "override" && !selected ? (
        <p className="text-body text-text-muted">Select a destination to disable.</p>
      ) : null}

      {tab === "diagnostics" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Transfer diagnostics</h2>
          <p className="mt-0 mb-4 text-body-sm text-text-muted">
            Heuristic filter of platform call index for failed / transfer-related outcomes
            (SA10-003 Should).
          </p>
          {failedCalls.length === 0 ? (
            <p className="m-0 text-body text-text-muted">No matching failed transfer outcomes.</p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Call</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">End reason</th>
                    <th className="border-0 px-2 py-2 text-left">Agency</th>
                    <th className="border-0 px-2 py-2 text-left">Started</th>
                  </tr>
                </thead>
                <tbody>
                  {failedCalls.map((row) => (
                    <tr key={row.id}>
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.id.slice(0, 8)}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.status || "—"}</td>
                      <td className="px-2 py-3 text-text-secondary">{row.end_reason || "—"}</td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.agency_id?.slice(0, 8) || "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.started_at || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-4">
            <ApiNote>
              Dedicated failed-transfer diagnostics endpoint is not available. This view filters
              GET /api/v1/platform/calls for transfer-related end reasons.
            </ApiNote>
          </div>
        </article>
      ) : null}
    </section>
  );
}
