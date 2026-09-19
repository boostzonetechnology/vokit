import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { formatWhen } from "@/features/payouts/lib/display";
import type { PayoutReceipt } from "@/features/payouts/types";

export function PayoutReceiptCard({ receipt }: { receipt: PayoutReceipt }) {
  const agency = receipt.agency_display_name || receipt.agency_legal_name || "Agency";
  const amount = formatMoneyMinor(receipt.amount_minor ?? 0, receipt.currency || "USD");

  const fields: Array<{ label: string; value: string }> = [
    { label: "Receipt number", value: receipt.receipt_number || "—" },
    { label: "Agency", value: agency },
    { label: "Payout request ID", value: receipt.payout_id || "—" },
    { label: "Payout method", value: receipt.method_label || "—" },
    { label: "Requested", value: formatWhen(receipt.requested_at) },
    { label: "Paid", value: formatWhen(receipt.paid_at) },
    { label: "Status", value: receipt.status || "paid" },
    { label: "Transaction reference", value: receipt.transaction_ref || "—" },
    { label: "Issuer", value: receipt.issuer || "Vokit" },
  ];

  return (
    <article
      className="overflow-hidden rounded-xl border border-border-default bg-surface shadow-subtle"
      aria-label="Payout receipt"
    >
      <header className="border-b border-border-default bg-canvas px-5 py-4">
        <p className="m-0 text-label uppercase tracking-[0.14em] text-text-muted">Vokit</p>
        <h3 className="m-0 mt-1 text-[1.35rem] font-bold tracking-[-0.02em] text-text-primary">
          Payout receipt
        </h3>
        <p className="m-0 mt-1 text-body-sm text-text-muted">
          Agency-visible confirmation · private admin proof excluded
        </p>
      </header>

      <div className="px-5 py-4">
        <p className="m-0 rounded-lg border border-border-default bg-canvas px-4 py-3 text-[1.35rem] font-semibold text-text-primary">
          {amount}
        </p>

        <dl className="m-0 mt-4 grid gap-3 sm:grid-cols-2">
          {fields.map((field) => (
            <div key={field.label}>
              <dt className="m-0 text-body-sm text-text-muted">{field.label}</dt>
              <dd className="m-0 mt-0.5 break-all font-medium text-text-primary">{field.value}</dd>
            </div>
          ))}
        </dl>

        <p className="m-0 mt-5 border-t border-border-default pt-3 text-body-sm text-text-muted">
          {receipt.disclaimer ||
            "This receipt confirms payout processing and is not the underlying banking proof."}
        </p>
      </div>
    </article>
  );
}
