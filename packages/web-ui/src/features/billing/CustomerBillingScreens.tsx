import { useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useCustomerBilling } from "./hooks/useCustomerBilling";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "paid") return "success";
  if (value === "open" || value === "pending" || value === "awaiting_webhook") return "warning";
  if (value === "failed" || value === "refunded" || value === "void") return "danger";
  return "neutral";
}

type CustomerUsageScreenProps = { mode?: "usage" };
type CustomerInvoicesScreenProps = { mode?: "invoices" | "payment-methods" };

export function CustomerUsageScreen(_props: CustomerUsageScreenProps = {}) {
  const { usageSummary, usage, error, message, loading, busy, reload, topUp } =
    useCustomerBilling();

  return (
    <section className="mx-auto max-w-[1100px]">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Usage & minutes
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Included, consumed, remaining · CU4
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton disabled={busy} onClick={() => void topUp()}>
            Purchase top-up
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

      {loading ? (
        <p className="text-body text-text-muted">Loading…</p>
      ) : (
        <div className="grid gap-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "Included remaining", value: usageSummary.included },
              { label: "Additional remaining", value: usageSummary.additional },
              { label: "Consumed", value: usageSummary.consumed },
              { label: "Total remaining", value: usageSummary.remaining },
            ].map((card) => (
              <article
                key={card.label}
                className="rounded-xl border border-border-default bg-surface px-4 py-3 shadow-subtle"
              >
                <p className="m-0 text-sm text-text-muted">{card.label}</p>
                <p className="m-0 mt-1 text-xl font-semibold text-text-primary">
                  {card.value} min
                </p>
              </article>
            ))}
          </div>

          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
              Minute lots
            </h2>
            {!usageSummary.lots.length ? (
              <p className="m-0 text-body text-text-muted">No minute lots on file.</p>
            ) : (
              <ul className="m-0 grid list-none gap-2 p-0">
                {usageSummary.lots.map((lot) => (
                  <li
                    key={lot.id}
                    className="flex justify-between gap-2 rounded-lg border border-border-default px-3 py-2 text-sm"
                  >
                    <span className="text-text-primary">
                      {lot.kind || "lot"} · {lot.id.slice(0, 8)}
                    </span>
                    <span className="text-text-muted">
                      {lot.remaining_minutes ?? 0} / {lot.granted_minutes ?? 0} min
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-3 mb-0 text-sm text-text-muted">
              Drain order: {(usage?.drain_order || []).join(" → ") || "—"}
              {usage?.overage_enabled ? " · overage enabled" : ""}
            </p>
            <ApiNote>
              CU4-002 — agent/date breakdown is not yet on the usage API; lots show package-level
              remaining.
            </ApiNote>
            <ApiNote>
              CU4-003 — top-up creates a Vokit minute package invoice (idempotent).
            </ApiNote>
          </article>
        </div>
      )}
    </section>
  );
}

export function CustomerInvoicesScreen({
  mode = "invoices",
}: CustomerInvoicesScreenProps) {
  const {
    invoices,
    methods,
    selectedInvoice,
    selectedInvoiceId,
    setSelectedInvoiceId,
    payIntent,
    error,
    message,
    loading,
    busy,
    statusFilter,
    setStatusFilter,
    query,
    setQuery,
    reload,
    payInvoice,
    downloadInvoiceJson,
  } = useCustomerBilling();

  const [tab, setTab] = useState<"invoices" | "methods" | "pay">(
    mode === "payment-methods" ? "methods" : "invoices",
  );

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Invoices & payments
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Pay, methods, receipts · CU5
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
        {(
          [
            { id: "invoices" as const, label: "Invoices" },
            { id: "methods" as const, label: "Payment methods" },
            { id: "pay" as const, label: "Pay / receipts" },
          ] as const
        ).map((item) => (
          <ActionButton
            key={item.id}
            variant={tab === item.id ? "secondary" : "outline"}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </ActionButton>
        ))}
      </div>

      {tab === "methods" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Payment methods
          </h2>
          {!methods.length ? (
            <p className="m-0 text-body text-text-muted">
              No payment methods returned. Hosted processor flows are not wired yet.
            </p>
          ) : (
            <ul className="m-0 grid list-none gap-2 p-0">
              {methods.map((row) => (
                <li
                  key={row.id}
                  className="rounded-lg border border-border-default px-3 py-2 text-sm"
                >
                  {row.brand || "Card"} ending {row.last4 || "••••"}
                  {row.is_default ? " · default" : ""}
                </li>
              ))}
            </ul>
          )}
          <ApiNote>
            CU5-003 — add/update through processor-hosted secure flow when the payment-methods API
            leaves stub mode.
          </ApiNote>
        </article>
      ) : (
        <>
          <div className="mb-4 grid gap-3 sm:grid-cols-2">
            <FormField
              label="Search"
              name="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <FormSelect
              label="Status"
              name="status"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="">All</option>
              <option value="open">Open</option>
              <option value="paid">Paid</option>
              <option value="failed">Failed</option>
              <option value="refunded">Refunded</option>
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
                        <p className="m-0 mt-1 text-sm text-text-muted">{row.id.slice(0, 8)}</p>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </article>

            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                Invoice actions
              </h2>
              {!selectedInvoice ? (
                <p className="m-0 text-body text-text-muted">Select an invoice.</p>
              ) : (
                <div className="grid gap-3">
                  <p className="m-0 text-sm text-text-muted">
                    {selectedInvoice.status} ·{" "}
                    {formatMoneyMinor(
                      selectedInvoice.total_minor ?? 0,
                      selectedInvoice.currency || "USD",
                    )}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {(selectedInvoice.status ?? "").toLowerCase() === "open" ? (
                      <ActionButton
                        disabled={busy}
                        onClick={() => void payInvoice(selectedInvoice.id)}
                      >
                        Pay with Stripe
                      </ActionButton>
                    ) : null}
                    <ActionButton
                      variant="outline"
                      onClick={() => downloadInvoiceJson(selectedInvoice)}
                    >
                      Download receipt
                    </ActionButton>
                  </div>
                  {payIntent?.invoice_id === selectedInvoice.id ? (
                    <pre className="m-0 overflow-auto rounded-lg border border-border-default bg-surface-muted p-3 text-xs">
                      {JSON.stringify(payIntent, null, 2)}
                    </pre>
                  ) : null}
                  <ApiNote>
                    CU5-002 / CU5-004 — pay creates a processor intent; receipts are invoice JSON
                    until a PDF endpoint ships.
                  </ApiNote>
                </div>
              )}
            </article>
          </div>
        </>
      )}
    </section>
  );
}

export function CustomerPaymentMethodsScreen() {
  return <CustomerInvoicesScreen mode="payment-methods" />;
}
