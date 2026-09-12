import { useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformIntegrations } from "./hooks/usePlatformIntegrations";

type Tab = "providers" | "connections" | "webhooks" | "disable";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "connected" || value === "active") return "success";
  if (value === "disabled" || value === "error") return "danger";
  return "neutral";
}

export function PlatformIntegrationsScreen() {
  const {
    providers,
    connections,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    agencyFilter,
    setAgencyFilter,
    reload,
    disableConnection,
  } = usePlatformIntegrations();

  const [tab, setTab] = useState<Tab>("connections");

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "providers", label: "Provider registry" },
    { id: "connections", label: "Connections" },
    { id: "webhooks", label: "Webhook logs" },
    { id: "disable", label: "Disable" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Integrations & webhooks
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA15-001–004 · Permission: integrations.review
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

      {tab === "providers" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Provider registry</h2>
          {providers.length === 0 ? (
            <p className="m-0 text-body text-text-muted">No providers returned.</p>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
              {providers.map((row) => (
                <div
                  key={row.provider}
                  className="rounded-xl border border-border-default bg-canvas px-3 py-3"
                >
                  <p className="m-0 font-semibold text-text-primary">{row.provider}</p>
                  <p className="mt-1 mb-0 text-body-sm text-text-muted">{row.category || "—"}</p>
                </div>
              ))}
            </div>
          )}
          <div className="mt-4">
            <ApiNote>
              SA15-001: GET /api/v1/platform/integration-providers lists available providers.
              Credential strategy is vault-backed (secret_ref). There is no platform POST to
              configure provider credentials; tenant connect happens on agency/customer routes.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "connections" || tab === "disable" ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 grid gap-3 lg:grid-cols-2">
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Search</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Agency id filter</span>
              <input
                value={agencyFilter}
                onChange={(event) => setAgencyFilter(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
          </div>
          <h2 className="m-0 mb-3 text-section text-text-primary">
            Tenant connections
            <span className="ml-2 text-body font-normal text-text-muted">
              ({connections.length})
            </span>
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading connections…</p>
          ) : connections.length === 0 ? (
            <p className="m-0 py-8 text-center text-body text-text-muted">No connections found.</p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Provider</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">Agency</th>
                    <th className="border-0 px-2 py-2 text-left">Customer</th>
                    <th className="border-0 px-2 py-2 text-left">Secret</th>
                  </tr>
                </thead>
                <tbody>
                  {connections.map((row) => (
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
                        {row.display_name || row.provider || row.id.slice(0, 8)}
                      </td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.agency_id?.slice(0, 8) || "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.customer_id?.slice(0, 8) || "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.has_secret ? "Present (masked)" : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-4">
            <ApiNote>
              Connection payloads expose has_secret only — raw credentials are never returned.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "disable" && selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">
            Disable {selected.display_name || selected.provider}
          </h2>
          <ActionButton
            disabled={busy || selected.status === "disabled"}
            onClick={() => void disableConnection(selected.id)}
          >
            Disable compromised connection
          </ActionButton>
        </article>
      ) : null}

      {tab === "disable" && !selected ? (
        <p className="text-body text-text-muted">Select a connection to disable.</p>
      ) : null}

      {tab === "webhooks" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Webhook delivery logs</h2>
          <ActionButton disabled title="API not available yet">
            Inspect platform webhook deliveries
          </ActionButton>
          <div className="mt-4">
            <ApiNote>
              SA15-003: webhook delivery/retry logs are agency-scoped
              (GET /api/v1/agency/webhooks/deliveries). There is no platform-wide webhook log API
              yet.
            </ApiNote>
          </div>
        </article>
      ) : null}
    </section>
  );
}
