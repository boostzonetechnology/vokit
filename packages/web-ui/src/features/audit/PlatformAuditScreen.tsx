import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformAudit } from "./hooks/usePlatformAudit";

function severityTone(severity?: string): BadgeTone {
  const value = (severity ?? "").toLowerCase();
  if (value === "critical" || value === "high") return "danger";
  if (value === "medium" || value === "warning") return "warning";
  if (value === "info" || value === "low") return "info";
  return "neutral";
}

export function PlatformAuditScreen() {
  const {
    events,
    selected,
    selectedId,
    setSelectedId,
    filters,
    setFilters,
    error,
    loading,
    reload,
    applyFilters,
    resetFilters,
  } = usePlatformAudit();

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Audit logs
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA17-001–003 · Permission: audit.view · Immutable
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

      <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {(
            [
              ["actor_id", "Actor id"],
              ["action", "Action"],
              ["entity_type", "Entity type"],
              ["entity_id", "Entity id"],
              ["agency_id", "Tenant / agency id"],
              ["customer_id", "Customer id"],
              ["ip", "IP"],
              ["severity", "Severity"],
              ["since", "Since (ISO)"],
              ["until", "Until (ISO)"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">{label}</span>
              <input
                value={filters[key]}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, [key]: event.target.value }))
                }
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton onClick={applyFilters}>Search</ActionButton>
          <ActionButton variant="outline" onClick={resetFilters}>
            Reset
          </ActionButton>
        </div>
      </article>

      <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <h2 className="m-0 mb-3 text-section text-text-primary">
          Events
          <span className="ml-2 text-body font-normal text-text-muted">({events.length})</span>
        </h2>
        {loading ? (
          <p className="m-0 text-body text-text-muted">Loading audit events…</p>
        ) : events.length === 0 ? (
          <p className="m-0 py-8 text-center text-body text-text-muted">No audit events found.</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">When</th>
                  <th className="border-0 px-2 py-2 text-left">Action</th>
                  <th className="border-0 px-2 py-2 text-left">Actor</th>
                  <th className="border-0 px-2 py-2 text-left">Entity</th>
                  <th className="border-0 px-2 py-2 text-left">Severity</th>
                  <th className="border-0 px-2 py-2 text-left">IP</th>
                </tr>
              </thead>
              <tbody>
                {events.map((row) => (
                  <tr
                    key={row.id}
                    className={
                      selectedId === row.id
                        ? "cursor-pointer bg-brand-subtle/40"
                        : "cursor-pointer hover:bg-canvas"
                    }
                    onClick={() => setSelectedId(row.id)}
                  >
                    <td className="px-2 py-3 text-text-secondary">{row.created_at || "—"}</td>
                    <td className="px-2 py-3 font-semibold text-text-primary">
                      {row.action || "—"}
                    </td>
                    <td className="px-2 py-3 text-text-secondary">
                      {row.actor_id?.slice(0, 8) || "—"}
                      {row.actor_role ? ` · ${row.actor_role}` : ""}
                    </td>
                    <td className="px-2 py-3 text-text-secondary">
                      {row.entity_type || "—"}
                      {row.entity_id ? `/${row.entity_id.slice(0, 8)}` : ""}
                    </td>
                    <td className="px-2 py-3">
                      <StatusBadge tone={severityTone(row.severity)}>
                        {row.severity || "—"}
                      </StatusBadge>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{row.ip || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      {selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Event detail</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <InfoTile label="Event id" value={selected.id} />
            <InfoTile label="Tenant" value={selected.tenant_id || "—"} />
            <InfoTile label="Customer" value={selected.customer_id || "—"} />
            <InfoTile label="Correlation" value={selected.correlation_id || "—"} />
            <InfoTile label="Reason" value={selected.reason || "—"} />
            <InfoTile label="Before" value={selected.before_summary || "—"} />
            <InfoTile label="After" value={selected.after_summary || "—"} />
          </div>
          {selected.payload != null ? (
            <pre className="mt-4 mb-0 overflow-auto rounded-xl bg-canvas p-4 text-body-sm text-text-secondary">
              {JSON.stringify(selected.payload, null, 2)}
            </pre>
          ) : null}
          <div className="mt-4 grid gap-2">
            <div className="flex flex-wrap gap-2">
              <ActionButton disabled title="Audit events are immutable">
                Edit event
              </ActionButton>
              <ActionButton variant="outline" disabled title="Audit events are immutable">
                Delete event
              </ActionButton>
            </div>
            <ApiNote>
              SA17-002: PATCH/DELETE /api/v1/platform/audit-events/{"{id}"} return audit_immutable.
              No normal UI may mutate audit events. SA17-003: payloads are summarized; raw secrets
              and full sensitive documents are not stored in audit logs.
            </ApiNote>
          </div>
        </article>
      ) : (
        <p className="text-body text-text-muted">Select an event to inspect summaries.</p>
      )}
    </section>
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
