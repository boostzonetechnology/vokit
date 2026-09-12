import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformPlans } from "./hooks/usePlatformPlans";
import type { PlanTermsInput, PlanVersion } from "./types";

type Tab = "entitlements" | "versions" | "assignment" | "grandfathering";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "archived") return "danger";
  return "neutral";
}

function termsFromForm(form: FormData): PlanTermsInput {
  return {
    price_minor: Number(form.get("price_minor") || 0),
    included_minutes: Number(form.get("included_minutes") || 0),
    allow_topups: form.get("allow_topups") === "on",
    topup_minutes: Number(form.get("topup_minutes") || 0),
    topup_price_minor: Number(form.get("topup_price_minor") || 0),
    overage_enabled: form.get("overage_enabled") === "on",
    overage_price_per_minute_minor: Number(form.get("overage_price_per_minute_minor") || 0),
    grace_seconds: Number(form.get("grace_seconds") || 0),
  };
}

function latestVersion(versions?: PlanVersion[]) {
  if (!versions?.length) return null;
  return [...versions].sort((a, b) => (b.version ?? 0) - (a.version ?? 0))[0];
}

export function PlatformPlansScreen() {
  const {
    plans,
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
    statusFilter,
    setStatusFilter,
    reload,
    createPlan,
    addVersion,
    archivePlan,
    assignToCustomer,
  } = usePlatformPlans();

  const [showCreate, setShowCreate] = useState(false);
  const [tab, setTab] = useState<Tab>("entitlements");
  const [assignCustomerId, setAssignCustomerId] = useState("");
  const [assignVersionId, setAssignVersionId] = useState("");

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createPlan({
        name: String(form.get("name") || ""),
        ...termsFromForm(form),
      });
      setShowCreate(false);
      event.currentTarget.reset();
      setTab("entitlements");
    } catch {
      /* message in hook */
    }
  }

  async function onAddVersion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    try {
      await addVersion(selected.id, termsFromForm(form));
      event.currentTarget.reset();
    } catch {
      /* message in hook */
    }
  }

  async function onAssign(event: FormEvent) {
    event.preventDefault();
    if (!assignCustomerId || !assignVersionId) return;
    try {
      await assignToCustomer(assignCustomerId, assignVersionId);
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "entitlements", label: "Entitlements" },
    { id: "versions", label: "Versions" },
    { id: "assignment", label: "Assignment" },
    { id: "grandfathering", label: "Grandfathering" },
  ];

  const selectedLatest = latestVersion(selected?.versions);

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Plans
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA11-001–004 · Permission: plans.manage
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close form" : "Create plan"}
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
          <h2 className="m-0 text-section text-text-primary">Create plan</h2>
          <p className="mt-1 mb-4 text-body-sm text-text-muted">
            Creates plan + version 1 entitlements via POST /api/v1/platform/plans.
          </p>
          <form className="grid gap-4" onSubmit={(event) => void onCreate(event)}>
            <Field label="Name" name="name" required />
            <TermsFields />
            <ApiNote>
              Agent/number/concurrency limits and feature flags are not accepted by the plan API
              yet. Billing cycle is implied by subscription assignment, not a plan field.
            </ApiNote>
            <div>
              <ActionButton type="submit" disabled={busy}>
                Create plan
              </ActionButton>
            </div>
          </form>
        </article>
      ) : null}

      <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <div className="mb-4 grid gap-3 lg:grid-cols-2">
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Search</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Plan name…"
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
              <option value="active">active</option>
              <option value="archived">archived</option>
            </select>
          </label>
        </div>

        <h2 className="m-0 mb-3 text-section text-text-primary">
          Plan catalog
          <span className="ml-2 text-body font-normal text-text-muted">({plans.length})</span>
        </h2>

        {loading ? (
          <p className="m-0 text-body text-text-muted">Loading plans…</p>
        ) : plans.length === 0 ? (
          <p className="m-0 py-10 text-center text-body text-text-muted">No plans yet.</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Plan</th>
                  <th className="border-0 px-2 py-2 text-left">Status</th>
                  <th className="border-0 px-2 py-2 text-left">Versions</th>
                  <th className="border-0 px-2 py-2 text-left">Latest price</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((row) => {
                  const latest = latestVersion(row.versions);
                  return (
                    <tr
                      key={row.id}
                      className={
                        selectedId === row.id
                          ? "cursor-pointer bg-brand-subtle/40"
                          : "cursor-pointer hover:bg-canvas"
                      }
                      onClick={() => {
                        setSelectedId(row.id);
                        setAssignVersionId(latest?.id || "");
                        setTab("entitlements");
                      }}
                    >
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.name || row.id.slice(0, 8)}
                      </td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.versions?.length ?? 0}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {typeof latest?.price_minor === "number"
                          ? formatMoneyMinor(latest.price_minor, latest.currency || "USD")
                          : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </article>

      {selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="m-0 text-section text-text-primary">
                {selected.name || selected.id.slice(0, 8)}
              </h2>
              <p className="mt-1 mb-0 text-body text-text-muted">{selected.id}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge tone={statusTone(selected.status)}>
                {selected.status || "unknown"}
              </StatusBadge>
              <ActionButton
                variant="outline"
                disabled={busy || selected.status === "archived"}
                onClick={() => void archivePlan(selected.id)}
              >
                Archive
              </ActionButton>
            </div>
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

          {tab === "entitlements" ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {selectedLatest ? (
                <>
                  <InfoTile
                    label="Price"
                    value={formatMoneyMinor(
                      selectedLatest.price_minor ?? 0,
                      selectedLatest.currency || "USD",
                    )}
                  />
                  <InfoTile
                    label="Included minutes"
                    value={String(selectedLatest.included_minutes ?? "—")}
                  />
                  <InfoTile
                    label="Top-ups"
                    value={
                      selectedLatest.allow_topups
                        ? `${selectedLatest.topup_minutes} min @ ${formatMoneyMinor(selectedLatest.topup_price_minor ?? 0)}`
                        : "Disabled"
                    }
                  />
                  <InfoTile
                    label="Overage"
                    value={
                      selectedLatest.overage_enabled
                        ? formatMoneyMinor(selectedLatest.overage_price_per_minute_minor ?? 0) +
                          "/min"
                        : "Disabled"
                    }
                  />
                  <InfoTile
                    label="Grace seconds"
                    value={String(selectedLatest.grace_seconds ?? "—")}
                  />
                </>
              ) : (
                <p className="m-0 text-body text-text-muted">No versions on this plan.</p>
              )}
              <div className="sm:col-span-2">
                <ApiNote>
                  Entitlement fields supported today: price, included minutes, top-ups, overage,
                  grace. Agent/number/concurrency limits and feature flags are not in the API.
                </ApiNote>
              </div>
            </div>
          ) : null}

          {tab === "versions" ? (
            <div className="grid gap-4">
              <div className="overflow-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-label uppercase text-text-muted">
                      <th className="border-0 px-2 py-2 text-left">Version</th>
                      <th className="border-0 px-2 py-2 text-left">Price</th>
                      <th className="border-0 px-2 py-2 text-left">Minutes</th>
                      <th className="border-0 px-2 py-2 text-left">Used</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(selected.versions ?? []).map((version) => (
                      <tr key={version.id}>
                        <td className="px-2 py-3 font-semibold text-text-primary">
                          v{version.version}
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {formatMoneyMinor(version.price_minor ?? 0, version.currency || "USD")}
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {version.included_minutes ?? "—"}
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {version.used ? "Yes" : "No"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <form className="grid gap-3 rounded-xl border border-border-default bg-canvas p-4" onSubmit={(event) => void onAddVersion(event)}>
                <h3 className="m-0 text-body font-semibold text-text-primary">Add version</h3>
                <TermsFields />
                <ActionButton type="submit" disabled={busy || selected.status === "archived"}>
                  Create version
                </ActionButton>
              </form>
            </div>
          ) : null}

          {tab === "assignment" ? (
            <form className="grid max-w-lg gap-3" onSubmit={(event) => void onAssign(event)}>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Customer</span>
                <select
                  value={assignCustomerId}
                  onChange={(event) => setAssignCustomerId(event.target.value)}
                  required
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  <option value="">Select customer</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.display_name || customer.id.slice(0, 8)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Plan version</span>
                <select
                  value={assignVersionId}
                  onChange={(event) => setAssignVersionId(event.target.value)}
                  required
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  <option value="">Select version</option>
                  {(selected.versions ?? []).map((version) => (
                    <option key={version.id} value={version.id}>
                      v{version.version} ·{" "}
                      {formatMoneyMinor(version.price_minor ?? 0, version.currency || "USD")}
                    </option>
                  ))}
                </select>
              </label>
              <ActionButton type="submit" disabled={busy}>
                Assign to customer
              </ActionButton>
              <ApiNote>
                Assignment uses POST /api/v1/platform/customers/{"{id}"}/subscription (permission:
                customers.create). Agency-level plan assignment is not a separate platform route.
              </ApiNote>
            </form>
          ) : null}

          {tab === "grandfathering" ? (
            <div className="grid gap-3">
              <p className="m-0 text-body text-text-secondary">
                Existing subscriptions keep the plan version they were assigned. Creating a new
                version does not migrate active subscribers automatically.
              </p>
              <ApiNote>
                SA11-004 (Should): there is no migrate-subscription endpoint. Grandfathering is the
                default runtime behavior when new versions are added.
              </ApiNote>
            </div>
          ) : null}
        </article>
      ) : (
        <p className="text-body text-text-muted">Select a plan to manage SA11 controls.</p>
      )}
    </section>
  );
}

function TermsFields() {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <Field label="Price (minor)" name="price_minor" defaultValue="10000" />
      <Field label="Included minutes" name="included_minutes" defaultValue="100" />
      <Field label="Top-up minutes" name="topup_minutes" defaultValue="50" />
      <Field label="Top-up price (minor)" name="topup_price_minor" defaultValue="2000" />
      <Field
        label="Overage price / min (minor)"
        name="overage_price_per_minute_minor"
        defaultValue="0"
      />
      <Field label="Grace seconds" name="grace_seconds" defaultValue="30" />
      <label className="m-0 flex items-center gap-2 font-normal">
        <input type="checkbox" name="allow_topups" defaultChecked />
        <span className="text-body text-text-secondary">Allow top-ups</span>
      </label>
      <label className="m-0 flex items-center gap-2 font-normal">
        <input type="checkbox" name="overage_enabled" />
        <span className="text-body text-text-secondary">Overage enabled</span>
      </label>
    </div>
  );
}

function Field({
  label,
  name,
  defaultValue,
  required,
}: {
  label: string;
  name: string;
  defaultValue?: string;
  required?: boolean;
}) {
  return (
    <label className="m-0 grid gap-1.5 font-normal">
      <span className="text-body-sm text-text-muted">{label}</span>
      <input
        name={name}
        required={required}
        defaultValue={defaultValue}
        className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
      />
    </label>
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
