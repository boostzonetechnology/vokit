import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { MetricGridSkeleton } from "@/components/ui/MetricCardSkeleton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { formatWhen } from "@/features/payouts/lib/display";
import {
  ledgerKindLabel,
  ledgerStateLabel,
  ledgerStateTone,
} from "@/features/payouts/lib/ledgerLabels";
import { payoutStatusTone } from "@/features/payouts/lib/status";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyPayoutMethods } from "./hooks/useAgencyPayoutMethods";
import { useAgencyWalletPayouts } from "./hooks/useAgencyWalletPayouts";

type Tab = "summary" | "ledger" | "withdraw" | "method";

const LEDGER_KINDS = [
  { value: "", label: "All kinds" },
  { value: "commission_earned", label: "Commission earned" },
  { value: "hold_released", label: "Hold released" },
  { value: "commission_reversal", label: "Reversal" },
  { value: "manual_credit", label: "Manual credit" },
  { value: "manual_debit", label: "Manual debit" },
  { value: "payout_reserved", label: "Payout reserved" },
  { value: "payout_paid", label: "Payout paid" },
  { value: "payout_released", label: "Payout released" },
] as const;

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
    ledgerKind,
    setLedgerKind,
    ledgerState,
    setLedgerState,
  } = useAgencyWalletPayouts();

  const methodsState = useAgencyPayoutMethods();
  const [tab, setTab] = useState<Tab>("summary");
  const [selectedMethodId, setSelectedMethodId] = useState("");
  const currency = buckets?.currency || "USD";

  const defaultMethodId =
    methodsState.usableMethods.find((row) => row.is_default)?.id ||
    methodsState.usableMethods[0]?.id ||
    "";

  async function onWithdraw(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const dollars = Number(form.get("amount") || 0);
    const amountMinor = Math.round(dollars * 100);
    const methodId = String(form.get("payout_method_id") || selectedMethodId || defaultMethodId);
    if (!methodId) {
      return;
    }
    try {
      await requestWithdrawal(amountMinor, methodId);
      event.currentTarget.reset();
      setSelectedMethodId("");
      setTab("summary");
      await methodsState.reload();
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

  const screenError = error || methodsState.error;
  const screenMessage = message || methodsState.message;

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Wallet
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Buckets, ledger, payout methods, withdrawals · AG11
          </p>
        </div>
        <ActionButton
          variant="secondary"
          onClick={() => {
            void reload();
            void methodsState.reload();
          }}
        >
          Refresh
        </ActionButton>
      </div>

      {screenError ? (
        <p className="mb-4 text-danger" role="alert">
          {screenError}
        </p>
      ) : null}
      {screenMessage ? (
        <p className="mb-4 text-body text-text-brand" role="status">
          {screenMessage}
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

      {loading && !buckets ? (
        <MetricGridSkeleton
          count={6}
          className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
        />
      ) : tab === "method" ? (
        <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
              Add bank details
            </h2>
            <p className="mt-0 mb-4 text-body text-text-muted">
              Save where Vokit should send withdrawals. Account numbers are masked after save.
            </p>
            <form className="grid gap-3" onSubmit={(event) => void methodsState.onSubmit(event)}>
              <FormField
                label="Beneficiary name"
                name="beneficiary_name"
                required
                value={methodsState.form.beneficiary_name}
                onChange={(event) =>
                  methodsState.updateField("beneficiary_name", event.target.value)
                }
                placeholder="Account holder legal name"
              />
              <FormField
                label="Account / IBAN"
                name="account_identifier"
                required
                value={methodsState.form.account_identifier}
                onChange={(event) =>
                  methodsState.updateField("account_identifier", event.target.value)
                }
                placeholder="Account number or IBAN"
              />
              <FormField
                label="Bank / provider"
                name="bank_name"
                required
                value={methodsState.form.bank_name}
                onChange={(event) => methodsState.updateField("bank_name", event.target.value)}
                placeholder="Bank name"
              />
              <div className="grid gap-3 sm:grid-cols-2">
                <FormField
                  label="Country (ISO)"
                  name="country"
                  required
                  maxLength={2}
                  value={methodsState.form.country}
                  onChange={(event) =>
                    methodsState.updateField("country", event.target.value.toUpperCase())
                  }
                  placeholder="US"
                />
                <FormField
                  label="Currency"
                  name="currency"
                  required
                  maxLength={3}
                  value={methodsState.form.currency || "USD"}
                  onChange={(event) =>
                    methodsState.updateField("currency", event.target.value.toUpperCase())
                  }
                  placeholder="USD"
                />
              </div>
              <label className="flex items-center gap-2 text-body text-text-secondary">
                <input
                  type="checkbox"
                  checked={Boolean(methodsState.form.is_default)}
                  onChange={(event) =>
                    methodsState.updateField("is_default", event.target.checked)
                  }
                />
                Set as default for withdrawals
              </label>
              <ActionButton type="submit" disabled={methodsState.busy}>
                Save payout method
              </ActionButton>
            </form>
            <div className="mt-4">
              <ApiNote>
                AG11-004 — methods are usable after KYC is verified. Pending and disabled methods stay
                in this list; only usable ones appear in the withdraw dropdown. Disable hides a
                method from withdraw without deleting it — Enable restores it.
              </ApiNote>
            </div>
          </article>

          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
              Saved methods ({methodsState.methods.length})
            </h2>
            {methodsState.loading && methodsState.methods.length === 0 ? (
              <p className="m-0 text-body text-text-muted">Loading…</p>
            ) : methodsState.methods.length === 0 ? (
              <p className="m-0 text-body text-text-muted">
                No payout methods yet. Add bank details to enable withdrawals.
              </p>
            ) : (
              <ul className="m-0 grid list-none gap-2 p-0">
                {methodsState.methods.map((row) => {
                  const isDisabled = (row.status ?? "").toLowerCase() === "disabled";
                  return (
                    <li
                      key={row.id}
                      className={`rounded-lg border border-border-default px-3 py-3${
                        isDisabled ? " bg-surface-muted/40 opacity-90" : ""
                      }`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <p className="m-0 font-medium text-text-primary">
                            {row.label || row.bank_name}
                          </p>
                          <p className="m-0 mt-1 text-sm text-text-muted">
                            {row.beneficiary_name}
                            {row.account_identifier_masked
                              ? ` · ${row.account_identifier_masked}`
                              : ""}
                            {row.country ? ` · ${row.country}` : ""}
                            {row.is_default ? " · Default" : ""}
                            {isDisabled ? " · Not available for withdraw" : ""}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <StatusBadge tone={payoutStatusTone(row.status)}>
                            {row.status || "—"}
                          </StatusBadge>
                          {isDisabled ? (
                            <ActionButton
                              variant="secondary"
                              disabled={methodsState.busy}
                              onClick={() => void methodsState.onEnable(row.id)}
                            >
                              Enable
                            </ActionButton>
                          ) : (
                            <ActionButton
                              variant="outline"
                              disabled={methodsState.busy}
                              onClick={() => void methodsState.onDisable(row.id)}
                            >
                              Disable
                            </ActionButton>
                          )}
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </article>
        </div>
      ) : tab === "withdraw" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Request withdrawal
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Available balance: {formatMoneyMinor(buckets?.available_minor ?? 0, currency)}. Only
            available funds can be withdrawn (AG11-003 / WAL-002).
          </p>
          {methodsState.usableMethods.length === 0 ? (
            <div className="grid gap-3">
              <p className="m-0 text-body text-text-muted">
                Add a usable payout method first (KYC verified). Pending methods cannot be used for
                withdrawal.
              </p>
              <ActionButton variant="secondary" onClick={() => setTab("method")}>
                Go to payout method
              </ActionButton>
            </div>
          ) : (
            <form className="grid max-w-lg gap-3" onSubmit={(event) => void onWithdraw(event)}>
              <FormField
                label="Amount (USD)"
                name="amount"
                type="number"
                step="0.01"
                min="0.01"
                required
              />
              <FormSelect
                label="Payout method"
                name="payout_method_id"
                required
                value={selectedMethodId || defaultMethodId}
                onChange={(event) => setSelectedMethodId(event.target.value)}
              >
                {methodsState.usableMethods.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.label || `${row.bank_name} · ${row.account_identifier_masked}`}
                    {row.is_default ? " (default)" : ""}
                  </option>
                ))}
              </FormSelect>
              <ActionButton
                type="submit"
                disabled={
                  busy ||
                  methodsState.busy ||
                  !(buckets?.available_minor ?? 0) ||
                  !(selectedMethodId || defaultMethodId)
                }
              >
                Request withdrawal
              </ActionButton>
            </form>
          )}
        </article>
      ) : tab === "ledger" ? (
        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Ledger ({entries.length})
          </h2>
          <div className="mb-3 grid gap-3 sm:grid-cols-2">
            <FormSelect
              label="Kind"
              name="ledger_kind"
              value={ledgerKind}
              onChange={(event) => setLedgerKind(event.target.value)}
            >
              {LEDGER_KINDS.map((item) => (
                <option key={item.value || "all"} value={item.value}>
                  {item.label}
                </option>
              ))}
            </FormSelect>
            <FormSelect
              label="Hold / availability"
              name="ledger_state"
              value={ledgerState}
              onChange={(event) => setLedgerState(event.target.value)}
            >
              <option value="">All states</option>
              <option value="on_hold">On hold</option>
              <option value="available">Available</option>
              <option value="frozen">Frozen</option>
              <option value="reversed">Reversed</option>
            </FormSelect>
          </div>
          {!entries.length ? (
            <p className="m-0 text-body text-text-muted">No ledger entries for this filter.</p>
          ) : (
            <ul className="m-0 grid max-h-[560px] list-none gap-2 overflow-auto p-0">
              {entries.map((row) => (
                <li
                  key={row.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                >
                  <div>
                    <p className="m-0 font-medium text-text-primary">
                      {ledgerKindLabel(row.kind)}
                    </p>
                    <p className="m-0 text-sm text-text-muted">
                      {row.reason || "—"}
                      {row.earned_at ? ` · earned ${formatWhen(row.earned_at)}` : ""}
                      {row.available_at ? ` · available ${formatWhen(row.available_at)}` : ""}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="m-0 font-medium text-text-primary">
                      {formatMoneyMinor(row.amount_minor ?? 0, row.currency || currency)}
                    </p>
                    {row.state ? (
                      <StatusBadge tone={ledgerStateTone(row.state)}>
                        {ledgerStateLabel(row.state)}
                      </StatusBadge>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
          <ApiNote>
            AG11-002 — earnings, reversals, adjustments, hold releases and payouts appear as ledger
            kinds with held/available state.
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
