import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyWalletPayouts } from "./hooks/useAgencyWalletPayouts";

type Tab = "summary" | "ledger" | "withdraw" | "method";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "available" || value === "paid") return "success";
  if (value === "held" || value === "pending" || value === "on_hold") return "warning";
  if (value === "frozen" || value === "reversed") return "danger";
  return "neutral";
}

export function AgencyWalletScreen() {
  const {
    buckets,
    entries,
    error,
    message,
    loading,
    busy,
    reload,
    requestWithdrawal,
  } = useAgencyWalletPayouts();

  const [tab, setTab] = useState<Tab>("summary");
  const currency = buckets?.currency || "USD";

  async function onWithdraw(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const dollars = Number(form.get("amount") || 0);
    const amountMinor = Math.round(dollars * 100);
    try {
      await requestWithdrawal(amountMinor, String(form.get("method_label") || "default"));
      event.currentTarget.reset();
      setTab("summary");
    } catch {
      /* hook message */
    }
  }

  const cards = [
    { label: "Available", value: buckets?.available_minor ?? 0 },
    { label: "On hold", value: buckets?.on_hold_minor ?? 0 },
    { label: "Frozen", value: buckets?.frozen_minor ?? 0 },
    { label: "Pending withdrawal", value: buckets?.withdrawal_pending_minor ?? 0 },
    { label: "Lifetime paid", value: buckets?.lifetime_paid_minor ?? 0 },
    { label: "Pending (accrual)", value: buckets?.pending_minor ?? 0 },
  ];

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "summary", label: "Summary" },
    { id: "ledger", label: "Ledger" },
    { id: "withdraw", label: "Withdraw" },
    { id: "method", label: "Payout method" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Wallet
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Buckets, ledger, withdrawals · AG11
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

      {loading ? (
        <p className="text-body text-text-muted" role="status">
          Loading…
        </p>
      ) : tab === "method" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Payout method
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Withdrawal requests accept an approved method label. A dedicated payout-methods CRUD
            API is not yet available; KYC/risk may require reverification before payouts.
          </p>
          <ApiNote>AG11-004 — manage method via label on withdrawal until methods API ships.</ApiNote>
        </article>
      ) : tab === "withdraw" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Request withdrawal
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Available balance: {formatMoneyMinor(buckets?.available_minor ?? 0, currency)}. Only
            available funds can be withdrawn (AG11-003).
          </p>
          <form className="grid max-w-lg gap-3" onSubmit={(event) => void onWithdraw(event)}>
            <FormField
              label="Amount (USD)"
              name="amount"
              type="number"
              step="0.01"
              min="0.01"
              required
            />
            <FormField
              label="Payout method label"
              name="method_label"
              required
              placeholder="Bank · ****1234"
            />
            <ActionButton type="submit" disabled={busy || !(buckets?.available_minor ?? 0)}>
              Request withdrawal
            </ActionButton>
          </form>
        </article>
      ) : tab === "ledger" ? (
        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Ledger ({entries.length})
          </h2>
          {!entries.length ? (
            <p className="m-0 text-body text-text-muted">No ledger entries.</p>
          ) : (
            <ul className="m-0 grid max-h-[560px] list-none gap-2 overflow-auto p-0">
              {entries.map((row) => (
                <li
                  key={row.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                >
                  <div>
                    <p className="m-0 font-medium text-text-primary">{row.kind}</p>
                    <p className="m-0 text-sm text-text-muted">
                      {row.reason || "—"}
                      {row.state ? ` · ${row.state}` : ""}
                      {row.available_at ? ` · available ${row.available_at}` : ""}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="m-0 font-medium text-text-primary">
                      {formatMoneyMinor(row.amount_minor ?? 0, row.currency || currency)}
                    </p>
                    {row.state ? (
                      <StatusBadge tone={statusTone(row.state)}>{row.state}</StatusBadge>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
          <ApiNote>
            AG11-002 — earnings, reversals, adjustments, hold releases and payouts appear as ledger
            kinds.
          </ApiNote>
        </article>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => (
            <article
              key={card.label}
              className="rounded-xl border border-border-default bg-surface px-4 py-3 shadow-subtle"
            >
              <p className="m-0 text-sm text-text-muted">{card.label}</p>
              <p className="m-0 mt-1 text-xl font-semibold text-text-primary">
                {formatMoneyMinor(card.value, currency)}
              </p>
            </article>
          ))}
          <ApiNote>
            AG11-001 — held, available, frozen, pending withdrawal and lifetime paid from wallet
            projection.
          </ApiNote>
        </div>
      )}
    </section>
  );
}
