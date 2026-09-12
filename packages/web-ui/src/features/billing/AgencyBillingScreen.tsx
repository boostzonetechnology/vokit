import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyBilling } from "./hooks/useAgencyBilling";

type Tab = "plans" | "invoices" | "revenue" | "payment";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "paid" || value === "active") return "success";
  if (value === "open" || value === "pending") return "warning";
  if (value === "void" || value === "failed") return "danger";
  return "neutral";
}

type AgencyBillingScreenProps = {
  initialTab?: Tab;
};

export function AgencyBillingScreen({ initialTab = "plans" }: AgencyBillingScreenProps) {
  const {
    plans,
    invoices,
    customers,
    customerFilter,
    setCustomerFilter,
    selectedInvoice,
    selectedInvoiceId,
    setSelectedInvoiceId,
    selectedPlan,
    selectedPlanId,
    setSelectedPlanId,
    revenue,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    customerName,
    reload,
    assignPlan,
  } = useAgencyBilling();

  const [tab, setTab] = useState<Tab>(initialTab);
  const [showAssign, setShowAssign] = useState(false);

  async function onAssign(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await assignPlan(String(form.get("customer_id") || ""), String(form.get("plan_version_id") || ""));
      setShowAssign(false);
      event.currentTarget.reset();
      setTab("invoices");
    } catch {
      /* hook message */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "plans", label: "Plan catalog" },
    { id: "invoices", label: "Customer invoices" },
    { id: "revenue", label: "Revenue view" },
    { id: "payment", label: "Payment destination" },
  ];

  const activeVersions =
    selectedPlan?.versions?.filter((version) => !version.used) ??
    selectedPlan?.versions ??
    [];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Plans & billing
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Catalog, invoices, commissionable revenue · AG10
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowAssign((v) => !v)}>
            {showAssign ? "Close" : "Assign plan"}
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

      {showAssign ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => void onAssign(event)}>
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
            <FormSelect label="Plan version" name="plan_version_id" required defaultValue="">
              <option value="" disabled>
                Select version
              </option>
              {plans.flatMap((plan) =>
                (plan.versions ?? []).map((version) => (
                  <option key={version.id} value={version.id}>
                    {plan.name} · v{version.version} ·{" "}
                    {formatMoneyMinor(version.price_minor ?? 0, version.currency || "USD")}
                  </option>
                )),
              )}
            </FormSelect>
            <ActionButton type="submit" disabled={busy}>
              Assign & create invoice
            </ActionButton>
          </form>
        </article>
      ) : null}

      {tab === "payment" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Payment destination
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Customer payments settle to the Vokit processor destination. Agencies cannot divert
            payment routing or change merchant settlement accounts.
          </p>
          <ApiNote>AG10-003 — no payment diversion controls are exposed by design.</ApiNote>
        </article>
      ) : tab === "revenue" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-4 text-[1.05rem] font-semibold text-text-primary">
            Revenue visibility
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-border-default px-4 py-3">
              <p className="m-0 text-sm text-text-muted">Gross customer billing (line totals)</p>
              <p className="m-0 mt-1 text-xl font-semibold text-text-primary">
                {formatMoneyMinor(revenue.gross_minor)}
              </p>
            </div>
            <div className="rounded-xl border border-border-default px-4 py-3">
              <p className="m-0 text-sm text-text-muted">Commissionable base</p>
              <p className="m-0 mt-1 text-xl font-semibold text-text-primary">
                {formatMoneyMinor(revenue.commissionable_minor)}
              </p>
            </div>
          </div>
          <ApiNote>
            AG10-004 — commissionable revenue is derived from invoice line flags, separate from
            gross billed totals. Wallet shows your earned commission separately.
          </ApiNote>
        </article>
      ) : tab === "invoices" ? (
        <>
          <div className="mb-4 grid gap-3 sm:grid-cols-2">
            <FormField
              label="Search"
              name="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
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
          </div>
          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                Invoices ({invoices.length})
              </h2>
              {loading ? (
                <p className="m-0 text-body text-text-muted">Loading…</p>
              ) : !invoices.length ? (
                <p className="m-0 text-body text-text-muted">No invoices.</p>
              ) : (
                <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
                  {invoices.map((row) => (
                    <li key={row.id}>
                      <button
                        type="button"
                        className={`w-full rounded-lg border px-3 py-2 text-left ${
                          selectedInvoiceId === row.id
                            ? "border-border-brand bg-surface-muted"
                            : "border-border-default"
                        }`}
                        onClick={() => setSelectedInvoiceId(row.id)}
                      >
                        <div className="flex justify-between gap-2">
                          <span className="font-medium text-text-primary">
                            {formatMoneyMinor(row.total_minor ?? 0, row.currency || "USD")}
                          </span>
                          <StatusBadge tone={statusTone(row.status)}>
                            {row.status || "—"}
                          </StatusBadge>
                        </div>
                        <p className="m-0 mt-1 text-sm text-text-muted">
                          {customerName(row.customer_id)} · {row.id.slice(0, 8)}
                        </p>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </article>
            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                Invoice detail
              </h2>
              {!selectedInvoice ? (
                <p className="m-0 text-body text-text-muted">Select an invoice.</p>
              ) : (
                <div className="grid gap-3 text-sm">
                  <p className="m-0 text-text-muted">
                    Status: {selectedInvoice.status || "—"}
                    {selectedInvoice.paid_at ? ` · paid ${selectedInvoice.paid_at}` : ""}
                  </p>
                  <ul className="m-0 grid list-none gap-2 p-0">
                    {(selectedInvoice.lines ?? []).map((line, index) => (
                      <li
                        key={`${selectedInvoice.id}-${index}`}
                        className="rounded-lg border border-border-default px-3 py-2"
                      >
                        <div className="flex justify-between gap-2">
                          <span>{line.description || `Line ${index + 1}`}</span>
                          <span>
                            {formatMoneyMinor(line.amount_minor ?? 0, selectedInvoice.currency || "USD")}
                          </span>
                        </div>
                        <p className="m-0 text-text-muted">
                          {line.commissionable ? "Commissionable" : "Non-commissionable"}
                        </p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </article>
          </div>
        </>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
              Available plans ({plans.length})
            </h2>
            {loading ? (
              <p className="m-0 text-body text-text-muted">Loading…</p>
            ) : !plans.length ? (
              <p className="m-0 text-body text-text-muted">No plans available for assignment.</p>
            ) : (
              <ul className="m-0 grid list-none gap-2 p-0">
                {plans.map((row) => (
                  <li key={row.id}>
                    <button
                      type="button"
                      className={`w-full rounded-lg border px-3 py-2 text-left ${
                        selectedPlanId === row.id
                          ? "border-border-brand bg-surface-muted"
                          : "border-border-default"
                      }`}
                      onClick={() => setSelectedPlanId(row.id)}
                    >
                      <div className="flex justify-between gap-2">
                        <span className="font-medium text-text-primary">{row.name}</span>
                        <StatusBadge tone={statusTone(row.status)}>{row.status || "—"}</StatusBadge>
                      </div>
                      <p className="m-0 mt-1 text-sm text-text-muted">
                        {(row.versions ?? []).length} version(s)
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </article>
          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">Plan versions</h2>
            {!selectedPlan ? (
              <p className="m-0 text-body text-text-muted">Select a plan.</p>
            ) : !activeVersions.length ? (
              <p className="m-0 text-body text-text-muted">No versions.</p>
            ) : (
              <ul className="m-0 grid list-none gap-2 p-0">
                {activeVersions.map((version) => (
                  <li
                    key={version.id}
                    className="rounded-lg border border-border-default px-3 py-2 text-sm"
                  >
                    <p className="m-0 font-medium text-text-primary">
                      v{version.version} ·{" "}
                      {formatMoneyMinor(version.price_minor ?? 0, version.currency || "USD")}
                    </p>
                    <p className="m-0 text-text-muted">
                      {version.included_minutes ?? 0} included minutes
                      {version.allow_topups ? " · top-ups allowed" : ""}
                    </p>
                  </li>
                ))}
              </ul>
            )}
            <ApiNote>AG10-001 — catalog is assignment/sale ready from active plan versions.</ApiNote>
          </article>
        </div>
      )}
    </section>
  );
}
