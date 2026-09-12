import { useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyWalletPayouts } from "./hooks/useAgencyWalletPayouts";

type Tab = "payouts" | "receipts" | "proof";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "paid") return "success";
  if (value === "requested" || value === "approved" || value === "processing") return "warning";
  if (value === "rejected" || value === "frozen") return "danger";
  return "neutral";
}

export function AgencyPayoutsScreen() {
  const {
    payouts,
    selectedPayout,
    selectedPayoutId,
    setSelectedPayoutId,
    receipt,
    setReceipt,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    reload,
    loadReceipt,
  } = useAgencyWalletPayouts();

  const [tab, setTab] = useState<Tab>("payouts");

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "payouts", label: "Payouts" },
    { id: "receipts", label: "Receipts" },
    { id: "proof", label: "Admin proof" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Payouts
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Requests, receipts · AG11
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
          <ActionButton
            key={item.id}
            variant={tab === item.id ? "secondary" : "outline"}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </ActionButton>
        ))}
      </div>

      {tab === "proof" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Private admin proof
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Platform payout proof remains inaccessible to agencies. Only non-sensitive receipt
            metadata is available after a payout is marked Paid.
          </p>
          <ApiNote>AG11-005 — proof endpoint always denies agency access by design.</ApiNote>
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
              <option value="requested">Requested</option>
              <option value="approved">Approved</option>
              <option value="processing">Processing</option>
              <option value="paid">Paid</option>
              <option value="rejected">Rejected</option>
              <option value="frozen">Frozen</option>
            </FormSelect>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                Payouts ({payouts.length})
              </h2>
              {loading ? (
                <p className="m-0 text-body text-text-muted">Loading…</p>
              ) : !payouts.length ? (
                <p className="m-0 text-body text-text-muted">No payouts yet.</p>
              ) : (
                <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
                  {payouts.map((row) => (
                    <li key={row.id}>
                      <button
                        type="button"
                        className={`w-full rounded-lg border px-3 py-2 text-left ${
                          selectedPayoutId === row.id
                            ? "border-border-brand bg-surface-muted"
                            : "border-border-default"
                        }`}
                        onClick={() => {
                          setSelectedPayoutId(row.id);
                          setReceipt(null);
                        }}
                      >
                        <div className="flex justify-between gap-2">
                          <span className="font-medium text-text-primary">
                            {formatMoneyMinor(row.amount_minor ?? 0, row.currency || "USD")}
                          </span>
                          <StatusBadge tone={statusTone(row.status)}>
                            {row.status || "—"}
                          </StatusBadge>
                        </div>
                        <p className="m-0 mt-1 text-sm text-text-muted">
                          {row.method_label || "—"}
                          {row.receipt_number ? ` · ${row.receipt_number}` : ""}
                        </p>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </article>

            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                {tab === "receipts" ? "Receipt" : "Detail"}
              </h2>
              {!selectedPayout ? (
                <p className="m-0 text-body text-text-muted">Select a payout.</p>
              ) : (
                <div className="grid gap-3 text-sm">
                  <dl className="m-0 grid gap-2">
                    <div>
                      <dt className="text-text-muted">Amount</dt>
                      <dd className="m-0 text-text-primary">
                        {formatMoneyMinor(
                          selectedPayout.amount_minor ?? 0,
                          selectedPayout.currency || "USD",
                        )}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-text-muted">Method</dt>
                      <dd className="m-0 text-text-primary">
                        {selectedPayout.method_label || "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-text-muted">Receipt #</dt>
                      <dd className="m-0 text-text-primary">
                        {selectedPayout.receipt_number || "Not generated yet"}
                      </dd>
                    </div>
                  </dl>
                  {selectedPayout.status === "paid" ? (
                    <ActionButton
                      disabled={busy}
                      onClick={() => {
                        void loadReceipt(selectedPayout.id).then(() => setTab("receipts"));
                      }}
                    >
                      View receipt
                    </ActionButton>
                  ) : null}
                  {receipt && receipt.payout_id === selectedPayout.id ? (
                    <pre className="m-0 overflow-auto rounded-lg border border-border-default bg-surface-muted p-3 text-xs text-text-primary">
                      {JSON.stringify(receipt, null, 2)}
                    </pre>
                  ) : null}
                  <ApiNote>
                    AG11-005 — agency-visible receipts only; download is JSON metadata until a file
                    export endpoint exists.
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
