import { useEffect, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { ListRowsSkeleton } from "@/components/ui/ListRowSkeleton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { PayoutReceiptCard } from "@/features/payouts/components/PayoutReceiptCard";
import { formatWhen, shortId } from "@/features/payouts/lib/display";
import { downloadPayoutReceiptPdf } from "@/features/payouts/lib/payoutReceiptDocument";
import { payoutStatusTone } from "@/features/payouts/lib/status";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { agencyPayoutProofFileUrl } from "@/features/payouts/services/wallet.service";
import { useAgencyWalletPayouts } from "./hooks/useAgencyWalletPayouts";

type Tab = "history" | "receipts" | "proof";

export function AgencyPayoutsScreen() {
  const {
    payouts,
    selectedPayout,
    selectedPayoutId,
    setSelectedPayoutId,
    receipt,
    setReceipt,
    proof,
    setProof,
    proofUnavailable,
    error,
    message,
    setMessage,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    reload,
    loadReceipt,
    ensureReceipt,
    loadProof,
  } = useAgencyWalletPayouts();

  const [tab, setTab] = useState<Tab>("history");

  const listRows = useMemo(() => {
    if (tab === "receipts") {
      return payouts.filter((row) => (row.status ?? "").toLowerCase() === "paid");
    }
    return payouts;
  }, [payouts, tab]);

  useEffect(() => {
    if (tab === "receipts") {
      setStatusFilter("paid");
    }
  }, [tab, setStatusFilter]);

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "history", label: "History" },
    { id: "receipts", label: "Receipts" },
    { id: "proof", label: "Admin proof" },
  ];

  function switchTab(next: Tab) {
    setTab(next);
    if (next === "history" && statusFilter === "paid") {
      setStatusFilter("");
    }
  }

  async function openReceipt(payoutId: string) {
    try {
      await loadReceipt(payoutId);
      setTab("receipts");
    } catch {
      /* message in hook */
    }
  }

  async function openProof(payoutId: string) {
    setSelectedPayoutId(payoutId);
    setProof(null);
    try {
      await loadProof(payoutId);
      setTab("proof");
    } catch {
      setTab("proof");
    }
  }

  async function onDownloadPdf(payoutId: string) {
    try {
      const data = await ensureReceipt(payoutId);
      downloadPayoutReceiptPdf(data);
      setMessage("Receipt PDF downloaded.");
      setTab("receipts");
    } catch {
      /* message in hook */
    }
  }

  const activeReceipt =
    receipt && selectedPayout && receipt.payout_id === selectedPayout.id ? receipt : null;
  const activeProof =
    proof && selectedPayout && proof.payout_id === selectedPayout.id ? proof : null;

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Payouts
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            History, receipts, and SA-shared proof · AG11-005
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
            onClick={() => switchTab(item.id)}
          >
            {item.label}
          </ActionButton>
        ))}
      </div>

      {tab === "proof" ? (
        <div className="grid gap-4 lg:grid-cols-[1fr_1.05fr]">
          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
              Payouts ({listRows.length})
            </h2>
            {loading && listRows.length === 0 ? (
              <ListRowsSkeleton rows={8} />
            ) : !listRows.length ? (
              <p className="m-0 text-body text-text-muted">No payouts yet.</p>
            ) : (
              <ul className="m-0 grid max-h-[560px] list-none gap-2 overflow-auto p-0">
                {listRows.map((row) => {
                  const selected = selectedPayoutId === row.id;
                  return (
                    <li key={row.id}>
                      <button
                        type="button"
                        className={`w-full rounded-lg border px-3 py-2.5 text-left transition ${
                          selected
                            ? "border-border-brand bg-surface-muted"
                            : "border-border-default hover:bg-canvas"
                        }`}
                        onClick={() => void openProof(row.id)}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="m-0 font-medium text-text-primary">
                              {formatMoneyMinor(row.amount_minor ?? 0, row.currency || "USD")}
                            </p>
                            <p className="m-0 mt-1 text-sm text-text-muted">
                              {row.method_label || "—"} · {shortId(row.id)}
                            </p>
                          </div>
                          <StatusBadge tone={payoutStatusTone(row.status)}>
                            {row.status || "—"}
                          </StatusBadge>
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </article>
          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
              Shared admin proof
            </h2>
            {!selectedPayout ? (
              <p className="m-0 text-body text-text-muted">
                Select a payout to check whether platform shared proof for it.
              </p>
            ) : busy && !activeProof && !proofUnavailable ? (
              <p className="m-0 text-body text-text-muted">Loading…</p>
            ) : activeProof ? (
              <div className="grid gap-3">
                {(activeProof.content_type ?? "").startsWith("image/") ? (
                  <img
                    src={agencyPayoutProofFileUrl(selectedPayout.id)}
                    alt="Shared payout proof"
                    className="max-h-72 w-full rounded-lg border border-border-default object-contain bg-canvas"
                  />
                ) : (
                  <a
                    href={agencyPayoutProofFileUrl(selectedPayout.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="text-body text-text-brand"
                  >
                    Open shared proof file
                  </a>
                )}
                <dl className="m-0 grid gap-2 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="text-text-muted">Content type</dt>
                    <dd className="m-0 font-medium text-text-primary">
                      {activeProof.content_type || "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Shared at</dt>
                    <dd className="m-0 font-medium text-text-primary">
                      {formatWhen(activeProof.agency_visible_at)}
                    </dd>
                  </div>
                </dl>
                <ApiNote>
                  Platform shared this payout&apos;s proof with your agency. Other payouts stay
                  private unless shared individually.
                </ApiNote>
              </div>
            ) : (
              <div className="grid gap-3">
                <p className="m-0 text-body text-text-muted">
                  Platform has not shared proof for this payout. You still have access to the
                  agency receipt after Paid.
                </p>
                <ApiNote>
                  Default is private (BR-009). Visibility is per payout, controlled by Super Admin.
                </ApiNote>
              </div>
            )}
          </article>
        </div>
      ) : (
        <>
          <div className="mb-4 grid gap-3 sm:grid-cols-2">
            <FormField
              label="Search"
              name="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Receipt #, method, status…"
            />
            <FormSelect
              label="Status"
              name="status"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              disabled={tab === "receipts"}
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

          <div className="grid gap-4 lg:grid-cols-[1fr_1.05fr]">
            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                {tab === "receipts" ? "Paid payouts" : "Payout history"} ({listRows.length})
              </h2>
              {loading && listRows.length === 0 ? (
                <ListRowsSkeleton rows={8} />
              ) : !listRows.length ? (
                <p className="m-0 text-body text-text-muted">
                  {tab === "receipts" ? "No paid payouts with receipts yet." : "No payouts yet."}
                </p>
              ) : (
                <ul className="m-0 grid max-h-[560px] list-none gap-2 overflow-auto p-0">
                  {listRows.map((row) => {
                    const selected = selectedPayoutId === row.id;
                    const paid = (row.status ?? "").toLowerCase() === "paid";
                    return (
                      <li key={row.id}>
                        <button
                          type="button"
                          className={`w-full rounded-lg border px-3 py-2.5 text-left transition ${
                            selected
                              ? "border-border-brand bg-surface-muted"
                              : "border-border-default hover:bg-canvas"
                          }`}
                          onClick={() => {
                            setSelectedPayoutId(row.id);
                            setReceipt(null);
                            if (tab === "receipts" && paid) {
                              void openReceipt(row.id);
                            }
                          }}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <p className="m-0 font-medium text-text-primary">
                                {formatMoneyMinor(row.amount_minor ?? 0, row.currency || "USD")}
                              </p>
                              <p className="m-0 mt-1 text-sm text-text-muted">
                                {row.method_label || "—"}
                                {row.receipt_number
                                  ? ` · ${row.receipt_number}`
                                  : ` · ${shortId(row.id)}`}
                              </p>
                              <p className="m-0 mt-0.5 text-sm text-text-muted">
                                {paid
                                  ? `Paid ${formatWhen(row.paid_at)}`
                                  : `Requested ${formatWhen(row.requested_at)}`}
                              </p>
                            </div>
                            <StatusBadge tone={payoutStatusTone(row.status)}>
                              {row.status || "—"}
                            </StatusBadge>
                          </div>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </article>

            <div className="grid gap-4 content-start">
              <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
                <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                  {tab === "receipts" ? "Receipt actions" : "Payout detail"}
                </h2>
                {!selectedPayout ? (
                  <p className="m-0 text-body text-text-muted">Select a payout from the list.</p>
                ) : (
                  <div className="grid gap-3">
                    <dl className="m-0 grid gap-2 text-sm sm:grid-cols-2">
                      <div>
                        <dt className="text-text-muted">Amount</dt>
                        <dd className="m-0 font-medium text-text-primary">
                          {formatMoneyMinor(
                            selectedPayout.amount_minor ?? 0,
                            selectedPayout.currency || "USD",
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-text-muted">Status</dt>
                        <dd className="m-0">
                          <StatusBadge tone={payoutStatusTone(selectedPayout.status)}>
                            {selectedPayout.status || "—"}
                          </StatusBadge>
                        </dd>
                      </div>
                      <div>
                        <dt className="text-text-muted">Method</dt>
                        <dd className="m-0 font-medium text-text-primary">
                          {selectedPayout.method_label || "—"}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-text-muted">Receipt #</dt>
                        <dd className="m-0 font-medium text-text-primary">
                          {selectedPayout.receipt_number || "Not generated yet"}
                        </dd>
                      </div>
                    </dl>
                    {(selectedPayout.status ?? "").toLowerCase() === "paid" ? (
                      <div className="flex flex-wrap gap-2">
                        <ActionButton
                          variant="secondary"
                          disabled={busy}
                          onClick={() => void openReceipt(selectedPayout.id)}
                        >
                          View receipt
                        </ActionButton>
                        <ActionButton
                          variant="outline"
                          disabled={busy}
                          onClick={() => void onDownloadPdf(selectedPayout.id)}
                        >
                          Download PDF
                        </ActionButton>
                        <ActionButton
                          variant="outline"
                          disabled={busy}
                          onClick={() => void openProof(selectedPayout.id)}
                        >
                          Check admin proof
                        </ActionButton>
                      </div>
                    ) : (
                      <ActionButton
                        variant="outline"
                        disabled={busy}
                        onClick={() => void openProof(selectedPayout.id)}
                      >
                        Check admin proof
                      </ActionButton>
                    )}
                  </div>
                )}
              </article>

              {tab === "receipts" || activeReceipt ? (
                activeReceipt ? (
                  <div className="grid gap-3">
                    <PayoutReceiptCard receipt={activeReceipt} />
                    <p className="m-0 text-sm text-text-muted">
                      Download PDF is an offline copy. Private proof is separate and only shown when
                      Super Admin shares it.
                    </p>
                  </div>
                ) : tab === "receipts" ? (
                  <p className="m-0 text-body text-text-muted">
                    Select a paid payout to preview and download its receipt.
                  </p>
                ) : null
              ) : null}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
