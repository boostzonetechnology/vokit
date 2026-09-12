import { FormEvent, useEffect, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformPayouts } from "./hooks/usePlatformPayouts";
import { PAYOUT_ACTIONS } from "./types";

type Tab = "wallet" | "queue" | "actions" | "proof" | "receipt" | "adjustment";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "paid" || value === "approved") return "success";
  if (value === "requested" || value === "processing") return "warning";
  if (value === "rejected" || value === "frozen") return "danger";
  return "neutral";
}

export function PlatformPayoutsScreen() {
  const {
    payouts,
    agencies,
    selected,
    selectedId,
    setSelectedId,
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
    loadProof,
    adjustWallet,
    freezeWallet,
  } = usePlatformPayouts();

  const [tab, setTab] = useState<Tab>("queue");
  const [transactionRef, setTransactionRef] = useState("");
  const currency = wallet?.currency || selected?.currency || "USD";

  useEffect(() => {
    if (selected?.agency_id && !agencyId) setAgencyId(selected.agency_id);
  }, [selected, agencyId, setAgencyId]);

  useEffect(() => {
    if (selectedId && (tab === "proof" || tab === "actions")) {
      void loadProof(selectedId);
    }
  }, [selectedId, tab, loadProof]);

  async function onProof(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    try {
      await uploadProof(selected.id, {
        object_ref: String(form.get("object_ref") || ""),
        content_type: String(form.get("content_type") || "application/pdf"),
        checksum: String(form.get("checksum") || ""),
      });
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
    { id: "wallet", label: "Wallet" },
    { id: "queue", label: "Payout queue" },
    { id: "actions", label: "Actions" },
    { id: "proof", label: "Proof" },
    { id: "receipt", label: "Receipt" },
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
            SA13-001–006 · Permissions: billing.view, payout.approve, wallet.adjust
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

      {tab === "queue" || tab === "actions" || tab === "proof" || tab === "receipt" ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 grid gap-3 lg:grid-cols-2">
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
            Payout queue
            <span className="ml-2 text-body font-normal text-text-muted">({payouts.length})</span>
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading payouts…</p>
          ) : payouts.length === 0 ? (
            <p className="m-0 py-8 text-center text-body text-text-muted">No payouts in this filter.</p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Payout</th>
                    <th className="border-0 px-2 py-2 text-left">Agency</th>
                    <th className="border-0 px-2 py-2 text-left">Amount</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">Receipt</th>
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
                      onClick={() => setSelectedId(row.id)}
                    >
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.id.slice(0, 8)}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.agency_id?.slice(0, 8) || "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {formatMoneyMinor(Number(row.amount_minor ?? 0), row.currency || "USD")}
                      </td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.receipt_number || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      ) : null}

      {tab === "actions" && selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">
            Actions · {selected.id.slice(0, 8)}
          </h2>
          <label className="mb-3 m-0 grid max-w-md gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Transaction ref (mark paid / process)</span>
            <input
              value={transactionRef}
              onChange={(event) => setTransactionRef(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            {PAYOUT_ACTIONS.map((action) => (
              <ActionButton
                key={action.value}
                variant="outline"
                disabled={busy}
                onClick={() => void runAction(selected.id, action.value, transactionRef)}
              >
                {action.label}
              </ActionButton>
            ))}
            <ActionButton
              disabled={busy}
              onClick={() => void markPaid(selected.id, transactionRef)}
            >
              Mark paid
            </ActionButton>
          </div>
          <div className="mt-4">
            <ApiNote>
              Actions use POST /api/v1/platform/payouts/{"{id}"}/action and /mark-paid (permission:
              payout.approve). Valid transitions are enforced server-side.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "proof" && selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Private proof</h2>
          {proof ? (
            <div className="mb-4 grid gap-2 sm:grid-cols-2">
              <InfoTile label="Object ref" value={proof.object_ref || "—"} />
              <InfoTile label="Content type" value={proof.content_type || "—"} />
              <InfoTile label="Checksum" value={proof.checksum || "—"} />
            </div>
          ) : (
            <p className="mb-4 mt-0 text-body text-text-muted">No proof on file yet.</p>
          )}
          <form className="grid max-w-xl gap-3" onSubmit={(event) => void onProof(event)}>
            <Field label="Object ref" name="object_ref" required />
            <Field label="Content type" name="content_type" defaultValue="application/pdf" />
            <Field label="Checksum" name="checksum" required />
            <ActionButton type="submit" disabled={busy}>
              Upload proof metadata
            </ActionButton>
          </form>
          <div className="mt-4">
            <ApiNote>
              Proof stores private object references only (not binary upload in this API). Agency
              proof GET returns 404 by design.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "receipt" && selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Receipt</h2>
          {selected.status === "paid" && selected.receipt_number ? (
            <div className="grid gap-2 sm:grid-cols-2">
              <InfoTile label="Receipt number" value={selected.receipt_number} />
              <InfoTile label="Paid at" value={selected.paid_at || "—"} />
              <InfoTile label="Transaction ref" value={selected.transaction_ref || "—"} />
              <InfoTile
                label="Amount"
                value={formatMoneyMinor(Number(selected.amount_minor ?? 0), selected.currency || "USD")}
              />
            </div>
          ) : (
            <p className="m-0 text-body text-text-muted">
              Receipt appears after mark paid. Agency-visible receipt is GET
              /api/v1/agency/payouts/{"{id}"}/receipt.
            </p>
          )}
        </article>
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
            <Field label="Amount (minor)" name="amount_minor" required defaultValue="1000" />
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
          <div className="mt-4">
            <ApiNote>
              POST /api/v1/platform/agencies/{"{id}"}/wallet/adjust requires wallet.adjust and a
              reason. Balances are never silently mutated.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {(tab === "actions" || tab === "proof" || tab === "receipt") && !selected ? (
        <p className="text-body text-text-muted">Select a payout from the queue.</p>
      ) : null}
    </section>
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
      <p className="mt-1 mb-0 break-all font-semibold text-text-primary">{value}</p>
    </div>
  );
}
