import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformNumbers } from "./hooks/usePlatformNumbers";

type Tab = "inventory" | "purchase" | "assignment" | "release" | "cost";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "available" || value === "assigned") return "success";
  if (value === "reserved") return "warning";
  if (value === "released") return "danger";
  return "neutral";
}

export function PlatformNumbersScreen() {
  const {
    numbers,
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
    countryFilter,
    setCountryFilter,
    reconcile,
    reload,
    stockNumber,
    purchaseNumber,
    releaseNumber,
    runReconcile,
  } = usePlatformNumbers();

  const [showStock, setShowStock] = useState(false);
  const [tab, setTab] = useState<Tab>("inventory");
  const [providerRelease, setProviderRelease] = useState(false);

  async function onStock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await stockNumber({
        e164: String(form.get("e164") || ""),
        country: String(form.get("country") || "US"),
        area: String(form.get("area") || ""),
        monthly_cost_minor: Number(form.get("monthly_cost_minor") || 0),
        provider: String(form.get("provider") || "platform"),
        provider_ref: String(form.get("provider_ref") || ""),
        capabilities: ["voice"],
      });
      setShowStock(false);
      event.currentTarget.reset();
    } catch {
      /* message in hook */
    }
  }

  async function onPurchase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await purchaseNumber(String(form.get("e164") || ""));
      event.currentTarget.reset();
      setTab("inventory");
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "inventory", label: "Inventory" },
    { id: "purchase", label: "Purchase" },
    { id: "assignment", label: "Assignment" },
    { id: "release", label: "Release" },
    { id: "cost", label: "Cost" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Phone numbers
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA9-001–005 · Permission: numbers.review
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" disabled={busy} onClick={() => void runReconcile()}>
            Reconcile
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowStock((v) => !v)}>
            {showStock ? "Close stock form" : "Stock number"}
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

      {reconcile ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <p className="m-0 text-body-sm text-text-muted">Last reconcile</p>
          <p className="mt-1 mb-0 text-body text-text-secondary">
            Expired reservations: {reconcile.expired_reservations ?? 0} · Provider orphans:{" "}
            {(reconcile.provider_orphans ?? []).length} · Local orphans:{" "}
            {(reconcile.local_orphans ?? []).length}
          </p>
        </article>
      ) : null}

      {showStock ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 text-section text-text-primary">Stock inventory</h2>
          <p className="mt-1 mb-4 text-body-sm text-text-muted">
            POST /api/v1/platform/phone-numbers without purchase flag.
          </p>
          <form className="grid gap-4" onSubmit={(event) => void onStock(event)}>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <Field label="E.164" name="e164" required placeholder="+15551234567" />
              <Field label="Country" name="country" defaultValue="US" />
              <Field label="Area" name="area" />
              <Field label="Monthly cost (minor)" name="monthly_cost_minor" defaultValue="500" />
              <Field label="Provider" name="provider" defaultValue="platform" />
              <Field label="Provider ref" name="provider_ref" />
            </div>
            <div>
              <ActionButton type="submit" disabled={busy}>
                Stock number
              </ActionButton>
            </div>
          </form>
        </article>
      ) : null}

      <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <div className="mb-4 grid gap-3 lg:grid-cols-3">
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Search</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="E.164, provider, agency…"
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
              <option value="available">available</option>
              <option value="reserved">reserved</option>
              <option value="assigned">assigned</option>
              <option value="released">released</option>
            </select>
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Country</span>
            <input
              value={countryFilter}
              onChange={(event) => setCountryFilter(event.target.value)}
              placeholder="US"
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
        </div>

        <h2 className="m-0 mb-3 text-section text-text-primary">
          Inventory
          <span className="ml-2 text-body font-normal text-text-muted">({numbers.length})</span>
        </h2>

        {loading ? (
          <p className="m-0 text-body text-text-muted">Loading numbers…</p>
        ) : numbers.length === 0 ? (
          <p className="m-0 py-10 text-center text-body text-text-muted">No numbers in inventory.</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Number</th>
                  <th className="border-0 px-2 py-2 text-left">Status</th>
                  <th className="border-0 px-2 py-2 text-left">Country</th>
                  <th className="border-0 px-2 py-2 text-left">Agency</th>
                  <th className="border-0 px-2 py-2 text-left">Monthly</th>
                  <th className="border-0 px-2 py-2 text-left">Provider</th>
                </tr>
              </thead>
              <tbody>
                {numbers.map((row) => (
                  <tr
                    key={row.id}
                    className={
                      selectedId === row.id
                        ? "cursor-pointer bg-brand-subtle/40"
                        : "cursor-pointer hover:bg-canvas"
                    }
                    onClick={() => {
                      setSelectedId(row.id);
                      setTab("inventory");
                    }}
                  >
                    <td className="px-2 py-3 font-semibold text-text-primary">
                      {row.e164 || row.id.slice(0, 8)}
                    </td>
                    <td className="px-2 py-3">
                      <StatusBadge tone={statusTone(row.status)}>
                        {row.status || "unknown"}
                      </StatusBadge>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{row.country || "—"}</td>
                    <td className="px-2 py-3 text-text-secondary">
                      {row.assigned_agency_id?.slice(0, 8) || "—"}
                    </td>
                    <td className="px-2 py-3 text-text-secondary">
                      {typeof row.monthly_cost_minor === "number"
                        ? formatMoneyMinor(row.monthly_cost_minor, row.currency || "USD")
                        : "—"}
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{row.provider || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      {selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="m-0 text-section text-text-primary">{selected.e164}</h2>
              <p className="mt-1 mb-0 text-body text-text-muted">{selected.id}</p>
            </div>
            <StatusBadge tone={statusTone(selected.status)}>
              {selected.status || "unknown"}
            </StatusBadge>
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
                onClick={() => setTab(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>

          {tab === "purchase" ? (
            <form className="grid max-w-md gap-3" onSubmit={(event) => void onPurchase(event)}>
              <p className="m-0 text-body text-text-secondary">
                Purchase a provider number into inventory (Idempotency-Key sent automatically).
              </p>
              <Field label="E.164 to purchase" name="e164" required placeholder="+15551234567" />
              <ActionButton type="submit" disabled={busy}>
                Purchase number
              </ActionButton>
            </form>
          ) : null}

          {tab === "inventory" && selected ? (
            <div className="grid gap-3 sm:grid-cols-2">
              <InfoTile label="Area" value={selected.area || "—"} />
              <InfoTile label="Capabilities" value={(selected.capabilities ?? []).join(", ") || "—"} />
              <InfoTile
                label="Customer"
                value={selected.assigned_customer_id?.slice(0, 8) || "—"}
              />
              <InfoTile label="Agent" value={selected.assigned_agent_id?.slice(0, 8) || "—"} />
              <InfoTile label="Reserved until" value={selected.reserved_until || "—"} />
            </div>
          ) : null}

          {tab === "assignment" && selected ? (
            <div className="grid gap-3">
              <InfoTile
                label="Assigned agency"
                value={selected.assigned_agency_id || "Unassigned"}
              />
              <InfoTile
                label="Assigned customer"
                value={selected.assigned_customer_id || "Unassigned"}
              />
              <InfoTile label="Assigned agent" value={selected.assigned_agent_id || "Unassigned"} />
              <ActionButton disabled title="API not available yet">
                Assign / reassign
              </ActionButton>
              <ApiNote>
                SA9-003 assignment is agency-scoped via POST /api/v1/agency/phone-numbers/reservations
                and /assignments. There is no platform assign/reassign route yet.
              </ApiNote>
            </div>
          ) : null}

          {tab === "release" && selected ? (
            <div className="grid gap-3">
              <label className="m-0 flex items-center gap-2 font-normal">
                <input
                  type="checkbox"
                  checked={providerRelease}
                  onChange={(event) => setProviderRelease(event.target.checked)}
                />
                <span className="text-body text-text-secondary">Also release at provider</span>
              </label>
              <ApiNote>
                Release requires confirm=true. Provider release permanently drops the number from
                the carrier; without it the number returns to inventory with retention warnings
                handled server-side.
              </ApiNote>
              <ActionButton
                disabled={busy}
                onClick={() => void releaseNumber(selected.id, providerRelease)}
              >
                Confirm release
              </ActionButton>
            </div>
          ) : null}

          {tab === "cost" && selected ? (
            <div className="grid gap-3 sm:grid-cols-2">
              <InfoTile
                label="Monthly cost"
                value={
                  typeof selected.monthly_cost_minor === "number"
                    ? formatMoneyMinor(selected.monthly_cost_minor, selected.currency || "USD")
                    : "—"
                }
              />
              <InfoTile label="Currency" value={selected.currency || "—"} />
              <InfoTile label="Provider" value={selected.provider || "—"} />
              <InfoTile label="Capabilities" value={(selected.capabilities ?? []).join(", ") || "—"} />
            </div>
          ) : null}

          {tab !== "purchase" && !selected ? (
            <p className="m-0 text-body text-text-muted">Select a number for this action.</p>
          ) : null}
        </article>
      ) : (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
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
          {tab === "purchase" ? (
            <form className="grid max-w-md gap-3" onSubmit={(event) => void onPurchase(event)}>
              <p className="m-0 text-body text-text-secondary">
                Purchase a provider number into inventory (Idempotency-Key sent automatically).
              </p>
              <Field label="E.164 to purchase" name="e164" required placeholder="+15551234567" />
              <ActionButton type="submit" disabled={busy}>
                Purchase number
              </ActionButton>
            </form>
          ) : (
            <p className="m-0 text-body text-text-muted">Select a number to manage SA9 controls.</p>
          )}
        </article>
      )}
    </section>
  );
}

function Field({
  label,
  name,
  defaultValue,
  required,
  placeholder,
}: {
  label: string;
  name: string;
  defaultValue?: string;
  required?: boolean;
  placeholder?: string;
}) {
  return (
    <label className="m-0 grid gap-1.5 font-normal">
      <span className="text-body-sm text-text-muted">{label}</span>
      <input
        name={name}
        required={required}
        defaultValue={defaultValue}
        placeholder={placeholder}
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
