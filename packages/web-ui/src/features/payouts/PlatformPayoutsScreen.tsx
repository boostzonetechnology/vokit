import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { TableSkeleton } from "@/components/ui/TableSkeleton";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { platformPayoutProofFileUrl } from "@/features/payouts/services/wallet.service";
import { usePlatformPayouts } from "./hooks/usePlatformPayouts";

type Tab = "payouts" | "wallet" | "adjustment";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "paid" || value === "approved") return "success";
  if (value === "requested" || value === "processing") return "warning";
  if (value === "rejected" || value === "frozen") return "danger";
  return "neutral";
}

function stepHint(status?: string, hasProof?: boolean): string {
  const value = (status ?? "").toLowerCase();
  if (value === "requested") return "Step 1 — Approve (or reject / freeze).";
  if (value === "approved" || value === "processing") {
    return hasProof
      ? "Step 3 — Enter bank/transaction ref and Mark paid."
      : "Step 2 — Upload proof image/PDF, then Mark paid.";
  }
  if (value === "paid") return "Done — receipt is available to the agency.";
  if (value === "rejected") return "Rejected — funds returned to available.";
  if (value === "frozen") return "Frozen — reject to release, or continue after review.";
  return "Select a payout to review.";
}

export function PlatformPayoutsScreen() {
  const {
    payouts,
    agencies,
    agencyLabel,
    selected,
    selectedId,
    selectPayout,
    agencyId,
    setAgencyId,
    wallet,
    proof,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    reload,
    runAction,
    markPaid,
    uploadProof,
    setProofAgencyVisible,
    adjustWallet,
    freezeWallet,
  } = usePlatformPayouts();

  const [tab, setTab] = useState<Tab>("payouts");
  const [transactionRef, setTransactionRef] = useState("");
  const [shareWithAgency, setShareWithAgency] = useState(false);
  const currency = wallet?.currency || selected?.currency || "USD";
  const status = (selected?.status ?? "").toLowerCase();
  const canApprove = status === "requested";
  const canMarkPaid = status === "approved" || status === "processing";
  const canUploadProof = Boolean(selected) && status !== "paid";

  async function onUploadProof(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    if (!(file instanceof File) || file.size === 0) {
      return;
    }
    try {
      await uploadProof(selected.id, file, shareWithAgency);
      event.currentTarget.reset();
    } catch {
      /* message in hook */
    }
  }

  async function onAdjust(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const targetAgency = String(form.get("agency_id") || agencyId);
    try {
      await adjustWallet({
        agencyId: targetAgency,
        amount_minor: Number(form.get("amount_minor") || 0),
        direction: String(form.get("direction") || "credit"),
        reason: String(form.get("reason") || ""),
      });
      event.currentTarget.reset();
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "payouts", label: "Payouts" },
    { id: "wallet", label: "Wallet" },
    { id: "adjustment", label: "Adjustment" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Wallet & payouts
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Review queue → approve → upload proof → mark paid
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

      {tab === "wallet" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <label className="mb-4 m-0 grid max-w-md gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Agency</span>
            <select
              value={agencyId}
              onChange={(event) => setAgencyId(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">Select agency</option>
              {agencies.map((agency) => (
                <option key={agency.id} value={agency.id}>
                  {agency.display_name || agency.id.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
          {agencyId && wallet ? (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <MetricCard
                label="Pending"
                value={formatMoneyMinor(Number(wallet.pending_minor ?? 0), currency)}
                hint="Not yet available"
              />
              <MetricCard
                label="Held"
                value={formatMoneyMinor(Number(wallet.on_hold_minor ?? 0), currency)}
                hint="Hold period"
              />
              <MetricCard
                label="Available"
                value={formatMoneyMinor(Number(wallet.available_minor ?? 0), currency)}
                hint="Withdrawable"
              />
              <MetricCard
                label="Frozen"
                value={formatMoneyMinor(Number(wallet.frozen_minor ?? 0), currency)}
                hint="Locked by risk/admin"
                accent="warning"
              />
              <MetricCard
                label="Requested"
                value={formatMoneyMinor(Number(wallet.withdrawal_pending_minor ?? 0), currency)}
                hint="In payout queue"
              />
              <MetricCard
                label="Paid"
                value={formatMoneyMinor(Number(wallet.lifetime_paid_minor ?? 0), currency)}
                hint="Lifetime paid"
                accent="success"
              />
            </div>
          ) : (
            <p className="m-0 text-body text-text-muted">Select an agency to view wallet buckets.</p>
          )}
          {agencyId ? (
            <div className="mt-4 flex flex-wrap gap-2">
              <ActionButton
                variant="outline"
                disabled={busy}
                onClick={() =>
                  void freezeWallet({
                    agencyId,
                    frozen: true,
                    reason: "Platform freeze from Wallet & payouts",
                  })
                }
              >
                Freeze wallet
              </ActionButton>
              <ActionButton
                variant="outline"
                disabled={busy}
                onClick={() =>
                  void freezeWallet({
                    agencyId,
                    frozen: false,
                    reason: "Platform unfreeze from Wallet & payouts",
                  })
                }
              >
                Unfreeze wallet
              </ActionButton>
            </div>
          ) : null}
        </article>
      ) : null}

      {tab === "payouts" ? (
        <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <div className="mb-4 grid gap-3 sm:grid-cols-2">
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Search</span>
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
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
                  <option value="open">Open queue</option>
                  <option value="">All</option>
                  <option value="requested">requested</option>
                  <option value="approved">approved</option>
                  <option value="processing">processing</option>
                  <option value="paid">paid</option>
                  <option value="rejected">rejected</option>
                  <option value="frozen">frozen</option>
                </select>
              </label>
            </div>
            <h2 className="m-0 mb-3 text-section text-text-primary">
              Queue
              <span className="ml-2 text-body font-normal text-text-muted">({payouts.length})</span>
            </h2>
            {loading && payouts.length === 0 ? (
              <TableSkeleton headers={["Payout", "Agency", "Amount", "Status"]} rows={6} />
            ) : payouts.length === 0 ? (
              <p className="m-0 py-8 text-center text-body text-text-muted">
                No payouts in this filter. Switch to All or paid to see history.
              </p>
            ) : (
              <div className="overflow-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-label uppercase text-text-muted">
                      <th className="border-0 px-2 py-2 text-left">Payout</th>
                      <th className="border-0 px-2 py-2 text-left">Agency</th>
                      <th className="border-0 px-2 py-2 text-left">Amount</th>
                      <th className="border-0 px-2 py-2 text-left">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payouts.map((row) => (
                      <tr
                        key={row.id}
                        className={
                          selectedId === row.id
                            ? "cursor-pointer bg-brand-subtle/40"
                            : "cursor-pointer hover:bg-canvas"
                        }
                        onClick={() => selectPayout(row)}
                      >
                        <td className="px-2 py-3">
                          <p className="m-0 font-semibold text-text-primary">
                            {row.receipt_number || row.id.slice(0, 8)}
                          </p>
                          <p className="m-0 text-body-sm text-text-muted">{row.id.slice(0, 8)}</p>
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {agencyLabel(row.agency_id)}
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {formatMoneyMinor(Number(row.amount_minor ?? 0), row.currency || "USD")}
                        </td>
                        <td className="px-2 py-3">
                          <StatusBadge tone={statusTone(row.status)}>
                            {row.status || "unknown"}
                          </StatusBadge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>

          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            {!selected ? (
              <p className="m-0 text-body text-text-muted">
                Select a payout from the queue to approve, attach proof, and mark paid.
              </p>
            ) : (
              <div className="grid gap-4">
                <div>
                  <h2 className="m-0 text-section text-text-primary">
                    {agencyLabel(selected.agency_id)} · {selected.id.slice(0, 8)}
                  </h2>
                  <p className="mt-1 mb-0 text-body text-text-muted">
                    {stepHint(selected.status, Boolean(proof))}
                  </p>
                  <div className="mt-2">
                    <StatusBadge tone={statusTone(selected.status)}>
                      {selected.status || "—"}
                    </StatusBadge>
                  </div>
                </div>

                <div className="grid gap-2 rounded-lg border border-border-default px-3 py-3 text-sm sm:grid-cols-2">
                  <div>
                    <p className="m-0 text-text-muted">Amount</p>
                    <p className="m-0 font-medium text-text-primary">
                      {formatMoneyMinor(
                        Number(selected.amount_minor ?? 0),
                        selected.currency || "USD",
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="m-0 text-text-muted">Method</p>
                    <p className="m-0 font-medium text-text-primary">
                      {selected.method_label || "—"}
                    </p>
                  </div>
                  {selected.receipt_number ? (
                    <div className="sm:col-span-2">
                      <p className="m-0 text-text-muted">Receipt</p>
                      <p className="m-0 font-medium text-text-primary">{selected.receipt_number}</p>
                    </div>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2">
                  {canApprove ? (
                    <ActionButton
                      disabled={busy}
                      onClick={() => void runAction(selected.id, "approve")}
                    >
                      Approve
                    </ActionButton>
                  ) : null}
                  {status === "approved" ? (
                    <ActionButton
                      variant="outline"
                      disabled={busy}
                      onClick={() => void runAction(selected.id, "process")}
                    >
                      Process
                    </ActionButton>
                  ) : null}
                  {status === "requested" ||
                  status === "approved" ||
                  status === "frozen" ? (
                    <ActionButton
                      variant="outline"
                      disabled={busy}
                      onClick={() => void runAction(selected.id, "reject")}
                    >
                      Reject
                    </ActionButton>
                  ) : null}
                  {status === "requested" ||
                  status === "approved" ||
                  status === "processing" ? (
                    <ActionButton
                      variant="outline"
                      disabled={busy}
                      onClick={() => void runAction(selected.id, "freeze")}
                    >
                      Freeze
                    </ActionButton>
                  ) : null}
                </div>

                {canUploadProof ? (
                  <div className="grid gap-3 border-t border-border-default pt-4">
                    <h3 className="m-0 text-body font-semibold text-text-primary">Proof</h3>
                    {proof ? (
                      <div className="grid gap-3">
                        {(proof.content_type ?? "").startsWith("image/") ? (
                          <img
                            src={platformPayoutProofFileUrl(selected.id)}
                            alt="Payout proof"
                            className="max-h-56 w-full rounded-lg border border-border-default object-contain bg-canvas"
                          />
                        ) : (
                          <a
                            href={platformPayoutProofFileUrl(selected.id)}
                            target="_blank"
                            rel="noreferrer"
                            className="text-body text-text-brand"
                          >
                            Open proof file
                          </a>
                        )}
                        <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border-default px-3 py-3">
                          <input
                            type="checkbox"
                            className="mt-1"
                            checked={Boolean(proof.agency_visible)}
                            disabled={busy}
                            onChange={(event) =>
                              void setProofAgencyVisible(selected.id, event.target.checked)
                            }
                          />
                          <span>
                            <span className="block font-medium text-text-primary">
                              Show proof to this agency
                            </span>
                            <span className="mt-0.5 block text-sm text-text-muted">
                              Only this payout. Off by default.
                            </span>
                          </span>
                        </label>
                      </div>
                    ) : (
                      <form className="grid gap-3" onSubmit={(event) => void onUploadProof(event)}>
                        <label className="m-0 grid gap-1.5 font-normal">
                          <span className="text-body-sm text-text-muted">
                            Image or PDF (max 5MB)
                          </span>
                          <input
                            name="file"
                            type="file"
                            accept="image/jpeg,image/png,image/webp,application/pdf"
                            required
                            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                          />
                        </label>
                        <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border-default px-3 py-3">
                          <input
                            type="checkbox"
                            className="mt-1"
                            checked={shareWithAgency}
                            onChange={(event) => setShareWithAgency(event.target.checked)}
                          />
                          <span className="text-sm text-text-primary">
                            Share with agency when uploading
                          </span>
                        </label>
                        <ActionButton type="submit" disabled={busy}>
                          Upload proof
                        </ActionButton>
                      </form>
                    )}
                  </div>
                ) : null}

                {canMarkPaid ? (
                  <div className="grid gap-3 border-t border-border-default pt-4">
                    <label className="m-0 grid gap-1.5 font-normal">
                      <span className="text-body-sm text-text-muted">
                        Transaction / bank reference
                      </span>
                      <input
                        value={transactionRef}
                        onChange={(event) => setTransactionRef(event.target.value)}
                        className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                        placeholder="e.g. ACH-12345"
                      />
                    </label>
                    <ActionButton
                      disabled={busy || !transactionRef.trim()}
                      onClick={() => void markPaid(selected.id, transactionRef.trim())}
                    >
                      Mark paid
                    </ActionButton>
                    {!proof ? (
                      <p className="m-0 text-sm text-text-muted">
                        Proof is usually required before mark paid (platform setting).
                      </p>
                    ) : null}
                  </div>
                ) : null}

                {status === "paid" ? (
                  <div className="grid gap-2 border-t border-border-default pt-4 text-sm">
                    <p className="m-0 text-text-muted">Receipt number</p>
                    <p className="m-0 font-medium text-text-primary">
                      {selected.receipt_number || "—"}
                    </p>
                    <p className="m-0 text-text-muted">Paid at</p>
                    <p className="m-0 font-medium text-text-primary">{selected.paid_at || "—"}</p>
                  </div>
                ) : null}
              </div>
            )}
          </article>
        </div>
      ) : null}

      {tab === "adjustment" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Manual wallet adjustment</h2>
          <form className="grid max-w-xl gap-3" onSubmit={(event) => void onAdjust(event)}>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Agency</span>
              <select
                name="agency_id"
                defaultValue={agencyId}
                required
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="">Select agency</option>
                {agencies.map((agency) => (
                  <option key={agency.id} value={agency.id}>
                    {agency.display_name || agency.id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Amount (minor)</span>
              <input
                name="amount_minor"
                required
                defaultValue="1000"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Direction</span>
              <select
                name="direction"
                defaultValue="credit"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="credit">credit</option>
                <option value="debit">debit</option>
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Reason (required)</span>
              <textarea
                name="reason"
                required
                rows={3}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <ActionButton type="submit" disabled={busy}>
              Record adjustment
            </ActionButton>
          </form>
        </article>
      ) : null}
    </section>
  );
}
