import { FormEvent, useState, type ReactNode } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatCount, formatMoneyMinor } from "@/features/dashboard/lib/format";
import { usePlatformCustomers } from "./hooks/usePlatformCustomers";
import { CUSTOMER_STATUS_ACTIONS } from "./types";

type Tab = "directory" | "balance" | "plan" | "status" | "impersonation";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active" || value === "paid") return "success";
  if (value === "open" || value === "pending") return "warning";
  if (value === "suspended" || value === "closed" || value === "failed") return "danger";
  return "neutral";
}

function ApiNote({ children }: { children: ReactNode }) {
  return (
    <p className="m-0 rounded-lg border border-dashed border-border-strong bg-canvas px-3 py-2 text-body-sm text-text-muted">
      {children}
    </p>
  );
}

export function PlatformCustomersScreen() {
  const {
    customers,
    agencies,
    planVersions,
    selectedId,
    setSelectedId,
    detail,
    invoices,
    calls,
    agents,
    openBalanceMinor,
    agencyName,
    agencyFilter,
    setAgencyFilter,
    statusFilter,
    setStatusFilter,
    query,
    setQuery,
    error,
    message,
    loading,
    busy,
    reloadList,
    createCustomer,
    setStatus,
    assignPlan,
  } = usePlatformCustomers();

  const [showCreate, setShowCreate] = useState(false);
  const [tab, setTab] = useState<Tab>("directory");

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createCustomer({
        agency_id: String(form.get("agency_id") || ""),
        display_name: String(form.get("display_name") || ""),
        owner_email: String(form.get("owner_email") || ""),
      });
      setShowCreate(false);
      event.currentTarget.reset();
      setTab("directory");
    } catch {
      /* message in hook */
    }
  }

  async function onAssignPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await assignPlan(String(form.get("plan_version_id") || ""));
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "directory", label: "Overview" },
    { id: "balance", label: "Balance" },
    { id: "plan", label: "Plan" },
    { id: "status", label: "Status" },
    { id: "impersonation", label: "Impersonation" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Customers
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA3-001–006 · Permissions: customers.view / customers.create · plans.manage ·
            billing.view
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ActionButton variant="secondary" onClick={() => void reloadList()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close form" : "Create customer"}
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
          <h2 className="m-0 text-section text-text-primary">Create customer</h2>
          <p className="mt-1 mb-4 text-body-sm text-text-muted">
            Super Admin may create a customer under any agency (SA3-002).
          </p>
          <form
            className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4 sm:items-end"
            onSubmit={(event) => void onCreate(event)}
          >
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Agency</span>
              <select
                name="agency_id"
                required
                defaultValue=""
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="" disabled>
                  Select agency
                </option>
                {agencies.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.display_name || row.id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </label>
            <Field label="Business name" name="display_name" required />
            <Field label="Owner email" name="owner_email" type="email" />
            <ActionButton type="submit" disabled={busy}>
              Create customer
            </ActionButton>
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
              placeholder="Name or id…"
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Agency</span>
            <select
              value={agencyFilter}
              onChange={(event) => setAgencyFilter(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">All agencies</option>
              {agencies.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.display_name || row.id.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Status</span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">All statuses</option>
              <option value="active">active</option>
              <option value="suspended">suspended</option>
              <option value="closed">closed</option>
            </select>
          </label>
        </div>

        <h2 className="m-0 mb-3 text-section text-text-primary">
          Global customer directory
          <span className="ml-2 text-body font-normal text-text-muted">({customers.length})</span>
        </h2>

        {loading ? (
          <p className="m-0 text-body text-text-muted">Loading customers…</p>
        ) : customers.length === 0 ? (
          <p className="m-0 py-10 text-center text-body text-text-muted">No customers found.</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Customer</th>
                  <th className="border-0 px-2 py-2 text-left">Agency</th>
                  <th className="border-0 px-2 py-2 text-left">Status</th>
                  <th className="border-0 px-2 py-2 text-left">Plan</th>
                  <th className="border-0 px-2 py-2 text-left">Balance</th>
                  <th className="border-0 px-2 py-2 text-left">Activity</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((row) => (
                  <tr
                    key={row.id}
                    className={
                      selectedId === row.id
                        ? "cursor-pointer bg-brand-subtle/40"
                        : "cursor-pointer hover:bg-canvas"
                    }
                    onClick={() => {
                      setSelectedId(row.id);
                      setTab("directory");
                    }}
                  >
                    <td className="px-2 py-3">
                      <p className="m-0 font-semibold text-text-primary">
                        {row.display_name || row.id.slice(0, 8)}
                      </p>
                      <p className="m-0 text-body-sm text-text-muted">{row.id.slice(0, 8)}</p>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">
                      {agencyName(row.agency_id)}
                    </td>
                    <td className="px-2 py-3">
                      <StatusBadge tone={statusTone(row.status)}>
                        {row.status || "unknown"}
                      </StatusBadge>
                    </td>
                    <td className="px-2 py-3 text-text-muted">—</td>
                    <td className="px-2 py-3 text-text-muted">—</td>
                    <td className="px-2 py-3 text-text-muted">—</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="mt-3 grid gap-2">
          <ApiNote>
            Directory search and filters for agency and status use GET
            /api/v1/platform/customers. Plan, balance, and activity columns are not included in
            the customer list payload yet, so those cells show as unavailable until the API
            returns them.
          </ApiNote>
        </div>
      </article>

      {detail ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="m-0 text-section text-text-primary">
                {detail.display_name || detail.id.slice(0, 8)}
              </h2>
              <p className="mt-1 mb-0 text-body text-text-muted">
                {agencyName(detail.agency_id)} · {detail.id}
              </p>
            </div>
            <StatusBadge tone={statusTone(detail.status)}>
              {detail.status || "unknown"}
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

          {tab === "directory" ? (
            <div className="grid gap-4">
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <InfoTile label="Agency" value={agencyName(detail.agency_id)} />
                <InfoTile label="Status" value={detail.status || "—"} />
                <InfoTile label="Agents" value={formatCount(agents.length)} />
                <InfoTile label="Recent calls" value={formatCount(calls.length)} />
              </div>
              <div>
                <h3 className="m-0 mb-2 text-section text-text-primary">Recent invoices</h3>
                {invoices.length === 0 ? (
                  <p className="m-0 text-body text-text-muted">No invoices for this customer.</p>
                ) : (
                  <div className="overflow-auto">
                    <table className="min-w-full">
                      <thead>
                        <tr className="text-label uppercase text-text-muted">
                          <th className="border-0 px-2 py-2 text-left">Status</th>
                          <th className="border-0 px-2 py-2 text-left">Amount</th>
                          <th className="border-0 px-2 py-2 text-left">Paid at</th>
                          <th className="border-0 px-2 py-2 text-left">Id</th>
                        </tr>
                      </thead>
                      <tbody>
                        {invoices.slice(0, 8).map((row) => (
                          <tr key={String(row.id)}>
                            <td className="px-2 py-3">
                              <StatusBadge tone={statusTone(String(row.status))}>
                                {String(row.status || "—")}
                              </StatusBadge>
                            </td>
                            <td className="px-2 py-3 text-text-secondary">
                              {formatMoneyMinor(
                                Number(row.total_minor ?? 0),
                                String(row.currency || "USD"),
                              )}
                            </td>
                            <td className="px-2 py-3 text-text-secondary">
                              {row.paid_at ? String(row.paid_at) : "—"}
                            </td>
                            <td className="px-2 py-3 text-text-muted">
                              {String(row.id).slice(0, 8)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ) : null}

          {tab === "balance" ? (
            <div className="grid gap-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <MetricCard
                  label="Open invoice balance"
                  value={formatMoneyMinor(openBalanceMinor, "USD")}
                  hint="Sum of open invoices (approximation)"
                  accent="brand"
                />
                <MetricCard
                  label="Minute balance"
                  value="—"
                  hint="Platform usage balance API not available"
                  accent="muted"
                />
              </div>
              <ActionButton disabled title="API not available yet">
                Adjust minute / monetary balance
              </ActionButton>
              <ApiNote>
                Customer minute/monetary ledger adjustment (SA3-003) is not available yet. The
                contracted endpoint POST /api/v1/platform/customers/{"{id}"}/minutes-adjustment is
                not implemented. Customer usage lots are only exposed on GET /api/v1/customer/usage
                for the customer portal session.
              </ApiNote>
            </div>
          ) : null}

          {tab === "plan" ? (
            <div className="grid gap-4">
              <form
                className="grid gap-3 sm:grid-cols-[1.4fr_auto] sm:items-end"
                onSubmit={(event) => void onAssignPlan(event)}
              >
                <label className="m-0 grid gap-1.5 font-normal">
                  <span className="text-body-sm text-text-muted">Plan version</span>
                  <select
                    name="plan_version_id"
                    required
                    defaultValue=""
                    className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                  >
                    <option value="" disabled>
                      Select plan version
                    </option>
                    {planVersions.map((row) => (
                      <option key={row.id} value={row.id}>
                        {row.plan_name} v{row.version} ·{" "}
                        {formatMoneyMinor(row.price_minor ?? 0, row.currency || "USD")} ·{" "}
                        {row.included_minutes ?? 0} min
                      </option>
                    ))}
                  </select>
                </label>
                <ActionButton type="submit" disabled={busy || planVersions.length === 0}>
                  Assign / change plan
                </ActionButton>
              </form>
              {planVersions.length === 0 ? (
                <ApiNote>
                  No plan versions loaded. GET /api/v1/platform/plans requires plans.manage and
                  must return nested versions.
                </ApiNote>
              ) : null}
              <ApiNote>
                Plan assignment uses POST /api/v1/platform/customers/{"{id}"}/subscription with
                plan_version_id (customers.create). A custom effective date and allowed overrides
                are not accepted by the current API. There is also no platform GET for the active
                subscription record yet.
              </ApiNote>
            </div>
          ) : null}

          {tab === "status" ? (
            <div className="grid gap-4">
              <p className="m-0 text-body text-text-secondary">
                Current status: <strong>{detail.status || "unknown"}</strong>
              </p>
              <div className="flex flex-wrap gap-2">
                {CUSTOMER_STATUS_ACTIONS.map((item) => (
                  <ActionButton
                    key={item.action}
                    variant={
                      item.action === "suspend" || item.action === "close"
                        ? "outline"
                        : "secondary"
                    }
                    disabled={busy}
                    onClick={() => void setStatus(item.action)}
                  >
                    {item.label}
                  </ActionButton>
                ))}
              </div>
              <ApiNote>
                Suspend / activate / close use POST /api/v1/platform/customers/{"{id}"}/status
                (authorized independently of agency status). Backend currently requires the
                customers.create permission for this action.
              </ApiNote>
            </div>
          ) : null}

          {tab === "impersonation" ? (
            <div className="grid gap-4">
              <ActionButton disabled title="API not available yet">
                Start secure impersonation
              </ActionButton>
              <ApiNote>
                Customer impersonation (SA3-006, Should) is not implemented. The permission
                impersonation.use exists in the role catalog, but no impersonation route, session
                banner, or audit workflow is exposed yet.
              </ApiNote>
            </div>
          ) : null}
        </article>
      ) : (
        <p className="text-body text-text-muted">Select a customer to manage SA3 controls.</p>
      )}
    </section>
  );
}

function Field({
  label,
  name,
  type = "text",
  required,
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
}) {
  return (
    <label className="m-0 grid gap-1.5 font-normal">
      <span className="text-body-sm text-text-muted">{label}</span>
      <input
        name={name}
        type={type}
        required={required}
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
