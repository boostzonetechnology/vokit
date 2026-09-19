import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { agencyStatusTone, formatAgencyStatus } from "@/features/agencies/lib/status";
import type { AgencyFinance } from "@/features/agencies/types";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";

export function AgencyFinancePanel({
  finance,
  currency,
}: {
  finance: AgencyFinance | null;
  currency: string;
}) {
  const buckets = finance?.buckets;
  const payouts = finance?.payouts ?? [];

  if (!finance) {
    return (
      <p className="m-0 text-body text-text-muted" role="status">
        Finance overview is unavailable for this agency.
      </p>
    );
  }

  return (
    <div className="grid gap-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          label="Subscription MRR"
          value={formatMoneyMinor(finance.mrr_minor, currency)}
          hint="Active monthly plan prices"
          accent="brand"
        />
        <MetricCard
          label="Commission on MRR"
          value={formatMoneyMinor(finance.commission_mrr_minor, currency)}
          hint="Using currently effective rate"
          accent="success"
        />
        <MetricCard
          label="Customer revenue (paid)"
          value={formatMoneyMinor(finance.customer_revenue_minor, currency)}
          hint="Trailing paid invoices"
          accent="info"
        />
        <MetricCard
          label="Commission earned"
          value={formatMoneyMinor(finance.commission_earned_minor, currency)}
          hint="Ledger commission earned"
          accent="muted"
        />
        <MetricCard
          label="Available"
          value={formatMoneyMinor(Number(buckets?.available_minor ?? 0), currency)}
          hint="Withdrawable wallet"
          accent="success"
        />
        <MetricCard
          label="On hold"
          value={formatMoneyMinor(Number(buckets?.on_hold_minor ?? 0), currency)}
          hint="Hold window funds"
          accent="warning"
        />
        <MetricCard
          label="Pending"
          value={formatMoneyMinor(Number(buckets?.pending_minor ?? 0), currency)}
          hint="Pending bucket"
          accent="muted"
        />
        <MetricCard
          label="Frozen"
          value={formatMoneyMinor(Number(buckets?.frozen_minor ?? 0), currency)}
          hint="Frozen wallet"
          accent="warning"
        />
        <MetricCard
          label="Pending withdrawal"
          value={formatMoneyMinor(Number(buckets?.withdrawal_pending_minor ?? 0), currency)}
          hint="Reserved in payout queue"
          accent="info"
        />
        <MetricCard
          label="Lifetime paid"
          value={formatMoneyMinor(Number(buckets?.lifetime_paid_minor ?? 0), currency)}
          hint="Completed payouts"
          accent="success"
        />
      </div>

      <div>
        <h3 className="m-0 mb-2 text-section text-text-primary">Payout history</h3>
        {payouts.length === 0 ? (
          <p className="m-0 text-body text-text-muted">No payouts for this agency.</p>
        ) : (
          <div className="overflow-auto rounded-xl border border-border-default">
            <table className="min-w-full">
              <thead>
                <tr className="bg-canvas text-label uppercase text-text-muted">
                  <th className="border-0 px-3 py-2.5 text-left">Status</th>
                  <th className="border-0 px-3 py-2.5 text-left">Amount</th>
                  <th className="border-0 px-3 py-2.5 text-left">Method</th>
                  <th className="border-0 px-3 py-2.5 text-left">Paid at</th>
                </tr>
              </thead>
              <tbody>
                {payouts.slice(0, 12).map((row, index) => (
                  <tr
                    key={String(row.id ?? `payout-${index}`)}
                    className="border-t border-border-default"
                  >
                    <td className="px-3 py-3">
                      <StatusBadge tone={agencyStatusTone(String(row.status))}>
                        {formatAgencyStatus(String(row.status || "—"))}
                      </StatusBadge>
                    </td>
                    <td className="px-3 py-3 text-text-secondary">
                      {formatMoneyMinor(
                        Number(row.amount_minor ?? 0),
                        String(row.currency || currency),
                      )}
                    </td>
                    <td className="px-3 py-3 text-text-secondary">
                      {row.method_label || "—"}
                    </td>
                    <td className="px-3 py-3 text-text-secondary">
                      {row.paid_at ? new Date(row.paid_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
