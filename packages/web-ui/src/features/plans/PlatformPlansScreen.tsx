import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { TableSkeleton } from "@/components/ui/TableSkeleton";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { PlanTermsFields } from "@/features/plans/components/PlanTermsFields";
import { usePlatformPlans } from "@/features/plans/hooks/usePlatformPlans";
import { termsFromForm } from "@/features/plans/lib/termsFromForm";
import { formatCapLimit, type PlanVersion } from "@/features/plans/types";

type Tab = "entitlements" | "versions" | "assignment" | "grandfathering";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "archived") return "danger";
  return "neutral";
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
    actionError,
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
      /* feedback in hook */
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
      /* feedback in hook */
    }
  }

  async function onAssign(event: FormEvent) {
    event.preventDefault();
    if (!assignCustomerId || !assignVersionId) return;
    try {
      await assignToCustomer(assignCustomerId, assignVersionId);
    } catch {
      /* feedback in hook */
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
            Versioned catalog with entitlements · Permission: plans.manage
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
      {actionError ? (
        <p className="mb-4 text-danger" role="alert">
          {actionError}
        </p>
      ) : null}
      {message ? (
        <p className="mb-4 text-body text-text-brand" role="status">
          {message}
        </p>
      ) : null}

      {showCreate ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-1 text-section text-text-primary">Create plan</h2>
          <p className="mt-0 mb-4 text-body-sm text-text-muted">
            Creates the plan and version 1. Caps of 0 mean unlimited. Empty integrations means all
            providers.
          </p>
          <form className="grid gap-4" onSubmit={(event) => void onCreate(event)}>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Name</span>
              <input
                name="name"
                required
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <PlanTermsFields availableIntegrations={selected?.available_integrations} />
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

        {loading && plans.length === 0 ? (
          <TableSkeleton headers={["Plan", "Status", "Versions", "Latest price"]} rows={8} />
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
                        {row.name || "Plan"}
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
              <h2 className="m-0 text-section text-text-primary">{selected.name || "Plan"}</h2>
              <p className="mt-1 mb-0 text-body text-text-muted">
                Versions keep purchase-time snapshots for active subscriptions.
              </p>
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
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
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
                        ? `${formatMoneyMinor(selectedLatest.overage_price_per_minute_minor ?? 0)}/min`
                        : "Disabled"
                    }
                  />
                  <InfoTile
                    label="Grace seconds"
                    value={String(selectedLatest.grace_seconds ?? "—")}
                  />
                  <InfoTile label="Max agents" value={formatCapLimit(selectedLatest.max_agents)} />
                  <InfoTile
                    label="Max phone numbers"
                    value={formatCapLimit(selectedLatest.max_phone_numbers)}
                  />
                  <InfoTile
                    label="Max concurrency"
                    value={formatCapLimit(selectedLatest.max_concurrency)}
                  />
                  <InfoTile
                    label="Recording"
                    value={selectedLatest.recording_allowed === false ? "Blocked" : "Allowed"}
                  />
                  <InfoTile
                    label="Integrations"
                    value={
                      selectedLatest.allowed_integrations?.length
                        ? selectedLatest.allowed_integrations.join(", ")
                        : "All providers"
                    }
                  />
                </>
              ) : (
                <p className="m-0 text-body text-text-muted">No versions on this plan.</p>
              )}
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
                      <th className="border-0 px-2 py-2 text-left">Caps</th>
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
                          A{formatCapLimit(version.max_agents)} · N
                          {formatCapLimit(version.max_phone_numbers)} · C
                          {formatCapLimit(version.max_concurrency)}
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {version.used ? "Yes" : "No"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <form
                className="grid gap-3 rounded-xl border border-border-default bg-canvas p-4"
                onSubmit={(event) => void onAddVersion(event)}
              >
                <h3 className="m-0 text-body font-semibold text-text-primary">Add version</h3>
                <PlanTermsFields availableIntegrations={selected.available_integrations} />
                <ActionButton type="submit" disabled={busy || selected.status === "archived"}>
                  Create version
                </ActionButton>
              </form>
            </div>
          ) : null}

          {tab === "assignment" ? (
            <form className="grid w-full min-w-0 gap-3 sm:max-w-xl" onSubmit={(event) => void onAssign(event)}>
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
                      {customer.display_name || "Customer"}
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
              <p className="m-0 text-body-sm text-text-muted">
                First assign only. Mid-cycle changes run from the customer detail Plan tab.
              </p>
              <ActionButton type="submit" disabled={busy}>
                Assign to customer
              </ActionButton>
            </form>
          ) : null}

          {tab === "grandfathering" ? (
            <p className="m-0 text-body text-text-secondary">
              Existing subscriptions keep the plan version they were assigned. Creating a new
              version does not migrate active subscribers automatically.
            </p>
          ) : null}
        </article>
      ) : (
        <p className="text-body text-text-muted">Select a plan to manage entitlements and versions.</p>
      )}
    </section>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-xl border border-border-default bg-canvas px-3 py-3">
      <p className="m-0 text-body-sm text-text-muted">{label}</p>
      <p className="mt-1 mb-0 break-words font-semibold text-text-primary">{value}</p>
    </div>
  );
}
