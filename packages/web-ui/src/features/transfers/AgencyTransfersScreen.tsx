import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyTransfers } from "./hooks/useAgencyTransfers";

type Tab = "destinations" | "rules" | "dtmf";

function statusTone(status?: string, disabled?: boolean): BadgeTone {
  if (disabled || status === "disabled") return "danger";
  if (status === "active") return "success";
  return "neutral";
}

export function AgencyTransfersScreen() {
  const {
    destinations,
    customers,
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
    statusFilter,
    setStatusFilter,
    customerName,
    reload,
    createDestination,
    disableDestination,
  } = useAgencyTransfers();

  const [tab, setTab] = useState<Tab>("destinations");
  const [showCreate, setShowCreate] = useState(false);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createDestination({
        customer_id: String(form.get("customer_id") || ""),
        kind: String(form.get("kind") || "e164"),
        label: String(form.get("label") || ""),
        target: String(form.get("target") || ""),
        no_answer_seconds: Number(form.get("no_answer_seconds") || 25),
      });
      setShowCreate(false);
      event.currentTarget.reset();
    } catch {
      /* hook message */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "destinations", label: "Destinations" },
    { id: "rules", label: "Rules" },
    { id: "dtmf", label: "DTMF" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Transfers
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Destinations, rules, DTMF · AG6
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close form" : "Add destination"}
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

      {showCreate ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Create verified destination
          </h2>
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => void onCreate(event)}>
            <FormSelect label="Customer" name="customer_id" required defaultValue="">
              <option value="" disabled>
                Select customer
              </option>
              {customers.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.display_name || row.id.slice(0, 8)}
                </option>
              ))}
            </FormSelect>
            <FormSelect label="Kind" name="kind" required defaultValue="e164">
              <option value="e164">E.164 phone</option>
              <option value="department">Department</option>
              <option value="queue">Queue</option>
              <option value="sip_client">SIP client</option>
            </FormSelect>
            <FormField label="Label" name="label" required placeholder="Front desk" />
            <FormField
              label="Target"
              name="target"
              required
              placeholder="+15551234567 or queue id"
            />
            <FormField
              label="No-answer seconds"
              name="no_answer_seconds"
              type="number"
              defaultValue={25}
              min={5}
            />
            <div className="flex items-end">
              <ActionButton type="submit" disabled={busy}>
                Create destination
              </ActionButton>
            </div>
          </form>
          <ApiNote>AG6-001 — destinations are customer-scoped and verified on create.</ApiNote>
        </article>
      ) : null}

      {tab === "rules" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Business hours & fallback rules
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Destinations support no-answer seconds today. Full business-hours, conditional and
            multi-step fallback rule editors are not yet exposed on the agency API.
          </p>
          <ApiNote>
            AG6-002 — configure no-answer on create for now; hours/fallback rule CRUD will land
            with the transfer rules endpoint.
          </ApiNote>
        </article>
      ) : tab === "dtmf" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Extension / DTMF
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            DTMF sequences for transfers are provider-dependent and not yet configurable in this
            portal.
          </p>
          <ApiNote>AG6-003 (Should) — pending provider-supported DTMF configuration API.</ApiNote>
        </article>
      ) : (
        <>
          <div className="mb-4 grid gap-3 sm:grid-cols-2">
            <FormField
              label="Search"
              name="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Label, target, kind…"
            />
            <FormSelect
              label="Customer"
              name="customer_filter"
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
              label="Status"
              name="status_filter"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="disabled">Disabled</option>
            </FormSelect>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                Destinations ({destinations.length})
              </h2>
              {loading ? (
                <p className="m-0 text-body text-text-muted" role="status">
                  Loading…
                </p>
              ) : !destinations.length ? (
                <p className="m-0 text-body text-text-muted">No destinations yet.</p>
              ) : (
                <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
                  {destinations.map((row) => (
                    <li key={row.id}>
                      <button
                        type="button"
                        className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                          selectedId === row.id
                            ? "border-border-brand bg-surface-muted"
                            : "border-border-default bg-surface hover:bg-surface-muted"
                        }`}
                        onClick={() => setSelectedId(row.id)}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium text-text-primary">
                            {row.label || row.id.slice(0, 8)}
                          </span>
                          <StatusBadge tone={statusTone(row.status, row.platform_disabled)}>
                            {row.platform_disabled ? "disabled" : row.status || "—"}
                          </StatusBadge>
                        </div>
                        <p className="m-0 mt-1 text-sm text-text-muted">
                          {row.kind} · {row.target || "—"} · {customerName(row.customer_id)}
                        </p>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </article>

            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">Detail</h2>
              {!selected ? (
                <p className="m-0 text-body text-text-muted">Select a destination.</p>
              ) : (
                <div className="grid gap-3">
                  <dl className="m-0 grid gap-2 text-sm">
                    <div>
                      <dt className="text-text-muted">Label</dt>
                      <dd className="m-0 text-text-primary">{selected.label}</dd>
                    </div>
                    <div>
                      <dt className="text-text-muted">Kind / target</dt>
                      <dd className="m-0 text-text-primary">
                        {selected.kind} · {selected.target || "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-text-muted">Customer</dt>
                      <dd className="m-0 text-text-primary">
                        {customerName(selected.customer_id)}
                      </dd>
                    </div>
                  </dl>
                  {selected.status !== "disabled" && !selected.platform_disabled ? (
                    <ActionButton
                      variant="outline"
                      disabled={busy}
                      onClick={() => {
                        if (
                          window.confirm(
                            `Disable destination “${selected.label || selected.id}”? Transfers using it will fail over.`,
                          )
                        ) {
                          void disableDestination(selected.id);
                        }
                      }}
                    >
                      Disable destination
                    </ActionButton>
                  ) : null}
                </div>
              )}
            </article>
          </div>
        </>
      )}
    </section>
  );
}
