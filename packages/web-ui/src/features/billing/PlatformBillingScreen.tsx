import { useEffect, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformBilling } from "./hooks/usePlatformBilling";
import type { BillingTab } from "./types";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "paid" || value === "captured" || value === "succeeded") return "success";
  if (value === "open" || value === "pending" || value === "processing") return "warning";
  if (value === "failed" || value === "void" || value === "lost") return "danger";
  return "neutral";
}

const TAB_FROM_ROUTE: Record<string, BillingTab> = {
  payments: "payments",
  invoices: "invoices",
  disputes: "disputes",
};

export function PlatformBillingScreen({ route = "payments" }: { route?: string }) {
  const {
    invoices,
    payments,
    disputes,
    selectedInvoice,
    selectedPayment,
    selectedInvoiceId,
    setSelectedInvoiceId,
    selectedPaymentId,
    setSelectedPaymentId,
    error,
    loading,
    query,
    setQuery,
    invoiceStatus,
    setInvoiceStatus,
    reload,
  } = usePlatformBilling();

  const [tab, setTab] = useState<BillingTab>(TAB_FROM_ROUTE[route] ?? "payments");

  useEffect(() => {
    setTab(TAB_FROM_ROUTE[route] ?? "payments");
  }, [route]);

  const tabs: Array<{ id: BillingTab; label: string }> = [
    { id: "payments", label: "Payments" },
    { id: "invoices", label: "Invoices" },
    { id: "refunds", label: "Refunds" },
    { id: "disputes", label: "Disputes" },
    { id: "adjustments", label: "Adjustments" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Billing & payments
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA12-001–005 · Permission: billing.view
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

      {(tab === "payments" || tab === "invoices" || tab === "disputes") && (
        <div className="mb-4 grid gap-3 lg:grid-cols-2">
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Search</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Id, customer, status…"
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          {tab === "invoices" ? (
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Invoice status</span>
              <select
                value={invoiceStatus}
                onChange={(event) => setInvoiceStatus(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="">All</option>
                <option value="open">open</option>
                <option value="paid">paid</option>
                <option value="void">void</option>
              </select>
            </label>
          ) : (
            <div />
          )}
        </div>
      )}

      {tab === "payments" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">
            Payments
            <span className="ml-2 text-body font-normal text-text-muted">({payments.length})</span>
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading payments…</p>
          ) : payments.length === 0 ? (
            <p className="m-0 py-10 text-center text-body text-text-muted">No payments yet.</p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Payment</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">Amount</th>
                    <th className="border-0 px-2 py-2 text-left">Processor</th>
                    <th className="border-0 px-2 py-2 text-left">Invoice</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map((row) => (
                    <tr
                      key={row.id}
                      className={
                        selectedPaymentId === row.id
                          ? "cursor-pointer bg-brand-subtle/40"
                          : "cursor-pointer hover:bg-canvas"
                      }
                      onClick={() => setSelectedPaymentId(row.id)}
                    >
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.id.slice(0, 8)}
                      </td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {typeof row.amount_minor === "number"
                          ? formatMoneyMinor(row.amount_minor, row.currency || "USD")
                          : "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.processor || "—"}</td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.invoice_id?.slice(0, 8) || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {selectedPayment ? (
            <div className="mt-4 grid gap-2 rounded-xl border border-border-default bg-canvas p-4 sm:grid-cols-2">
              <InfoTile label="Payment id" value={selectedPayment.id} />
              <InfoTile label="Customer" value={selectedPayment.customer_id || "—"} />
              <InfoTile label="Agency" value={selectedPayment.agency_id || "—"} />
              <InfoTile label="Allocation invoice" value={selectedPayment.invoice_id || "—"} />
            </div>
          ) : null}
        </article>
      ) : null}

      {tab === "invoices" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="m-0 text-section text-text-primary">
              Invoices
              <span className="ml-2 text-body font-normal text-text-muted">
                ({invoices.length})
              </span>
            </h2>
            <ActionButton disabled title="API not available yet">
              Generate invoice
            </ActionButton>
          </div>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading invoices…</p>
          ) : invoices.length === 0 ? (
            <p className="m-0 py-10 text-center text-body text-text-muted">No invoices yet.</p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Invoice</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">Total</th>
                    <th className="border-0 px-2 py-2 text-left">Customer</th>
                    <th className="border-0 px-2 py-2 text-left">Paid at</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((row) => (
                    <tr
                      key={row.id}
                      className={
                        selectedInvoiceId === row.id
                          ? "cursor-pointer bg-brand-subtle/40"
                          : "cursor-pointer hover:bg-canvas"
                      }
                      onClick={() => setSelectedInvoiceId(row.id)}
                    >
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.id.slice(0, 8)}
                      </td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {typeof row.total_minor === "number"
                          ? formatMoneyMinor(row.total_minor, row.currency || "USD")
                          : "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.customer_id?.slice(0, 8) || "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.paid_at || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {selectedInvoice ? (
            <div className="mt-4 grid gap-3">
              <div className="grid gap-2 rounded-xl border border-border-default bg-canvas p-4 sm:grid-cols-2">
                <InfoTile label="Invoice id" value={selectedInvoice.id} />
                <InfoTile label="Agency" value={selectedInvoice.agency_id || "—"} />
              </div>
              <ApiNote>
                Platform can view invoices via GET /api/v1/platform/invoices. Generate/reconcile
                actions are not exposed as dedicated platform endpoints yet. Invoices are created
                by subscription assignment and related billing flows.
              </ApiNote>
            </div>
          ) : null}
        </article>
      ) : null}

      {tab === "refunds" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Refunds</h2>
          <p className="mt-0 mb-4 text-body text-text-secondary">
            Initiate or record refunds subject to permission and processor support.
          </p>
          <ActionButton disabled title="API not available yet">
            Initiate refund
          </ActionButton>
          <div className="mt-4">
            <ApiNote>
              SA12-003: no platform refund endpoint is available. Processor refunds are not exposed
              through the control-plane API yet.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "disputes" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">
            Disputes / chargebacks
            <span className="ml-2 text-body font-normal text-text-muted">({disputes.length})</span>
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading disputes…</p>
          ) : disputes.length === 0 ? (
            <p className="m-0 py-10 text-center text-body text-text-muted">No disputes yet.</p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Event</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">Kind</th>
                    <th className="border-0 px-2 py-2 text-left">Processor</th>
                    <th className="border-0 px-2 py-2 text-left">Customer</th>
                  </tr>
                </thead>
                <tbody>
                  {disputes.map((row) => (
                    <tr key={row.event_id || `${row.processor}-${row.customer_id}`}>
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.event_id || "—"}
                      </td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.kind || "—"}</td>
                      <td className="px-2 py-3 text-text-secondary">{row.processor || "—"}</td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.customer_id?.slice(0, 8) || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-4">
            <ApiNote>
              Dispute list comes from GET /api/v1/platform/disputes (chargeback risk events).
              Commission-impact adjustment tooling is not paired to this list yet.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "adjustments" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Manual adjustments</h2>
          <p className="mt-0 mb-4 text-body text-text-secondary">
            Reasoned ledger adjustments must never silently mutate balances.
          </p>
          <ActionButton disabled title="Use Agencies → Financial for wallet adjust">
            Create ledger adjustment
          </ActionButton>
          <div className="mt-4">
            <ApiNote>
              SA12-005: customer invoice ledger adjustments are not exposed. Agency wallet
              adjustments use POST /api/v1/platform/agencies/{"{id}"}/wallet/adjust (permission:
              wallet.adjust) from the Agencies financial tab — requires a reason.
            </ApiNote>
          </div>
        </article>
      ) : null}
    </section>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="m-0 text-body-sm text-text-muted">{label}</p>
      <p className="mt-1 mb-0 break-all font-semibold text-text-primary">{value}</p>
    </div>
  );
}
