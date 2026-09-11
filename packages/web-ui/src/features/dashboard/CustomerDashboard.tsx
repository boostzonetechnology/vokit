import { useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { DualLineChart, useInvoiceSeries } from "./components/DualLineChart";
import { useDashboardBundle } from "./hooks/useDashboardBundle";
import {
  formatCount,
  formatMoneyMinor,
  kpiValue,
  periodLabel,
} from "./lib/format";

export function CustomerDashboard({ onNavigate }: { onNavigate: (href: string) => void }) {
  const [period, setPeriod] = useState("30d");
  const { data, invoices, paymentMethods, error, loading } = useDashboardBundle(
    "customer",
    period,
    "UTC",
  );
  const spendSeries = useInvoiceSeries(invoices);

  const openTotal = useMemo(
    () =>
      invoices
        .filter((row) => (row.status ?? "").toLowerCase() === "open")
        .reduce((sum, row) => sum + Number(row.total_minor ?? row.amount_minor ?? 0), 0),
    [invoices],
  );

  const paidThisPeriod = useMemo(
    () =>
      invoices
        .filter((row) => (row.status ?? "").toLowerCase() === "paid")
        .reduce((sum, row) => sum + Number(row.total_minor ?? row.amount_minor ?? 0), 0),
    [invoices],
  );

  const nextInvoice = useMemo(() => {
    return invoices
      .filter((row) => (row.status ?? "").toLowerCase() === "open")
      .sort((a, b) => String(a.due_at ?? a.created_at ?? "").localeCompare(String(b.due_at ?? b.created_at ?? "")))[0];
  }, [invoices]);

  const defaultMethod = paymentMethods.find((row) => row.is_default) ?? paymentMethods[0];

  if (loading && !data) {
    return <p className="text-body text-text-muted">Loading dashboard…</p>;
  }
  if (error && !data) {
    return (
      <p className="text-danger" role="alert">
        {error}
      </p>
    );
  }
  if (!data) return null;

  const minutesRemaining = Number(kpiValue(data, "minutes_remaining") ?? 0);
  const openInvoices = Number(kpiValue(data, "open_invoices") ?? 0);
  const plan = String(kpiValue(data, "plan") ?? "none");
  const hasSubscription = plan.toLowerCase() !== "none";
  const month = new Date(data.period.end).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Account overview
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Customer portal • Updated just now
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="m-0 font-normal" htmlFor="customer-period">
            <span className="sr-only">Billing period</span>
            <select
              id="customer-period"
              value={period}
              onChange={(event) => setPeriod(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body text-text-secondary"
              aria-label={periodLabel(period)}
            >
              <option value="today">Today</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="mtd">Month to date</option>
            </select>
          </label>
          <ActionButton variant="outline" onClick={() => onNavigate("#/invoices")}>
            Download statement
          </ActionButton>
          <ActionButton onClick={() => onNavigate("#/payment-methods")}>
            Add payment method
          </ActionButton>
        </div>
      </div>

      <div className="grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Current balance"
            value={formatMoneyMinor(openTotal, "USD")}
            hint={
              openInvoices > 0
                ? `${openInvoices} open invoice${openInvoices === 1 ? "" : "s"} due`
                : "$0 due · wallet credits not in API"
            }
            accent="brand"
            onClick={() => onNavigate("#/invoices")}
          />
          <MetricCard
            label="This month"
            value={formatMoneyMinor(paidThisPeriod, "USD")}
            hint={`${formatCount(minutesRemaining)} minutes remaining`}
            accent="success"
            onClick={() => onNavigate("#/usage")}
          />
          <MetricCard
            label="Active subscriptions"
            value={hasSubscription ? "1" : "0"}
            hint={hasSubscription ? `Plan: ${plan}` : "No active plan (count API missing)"}
            accent="muted"
            onClick={() => onNavigate("#/invoices")}
          />
          <MetricCard
            label="Next invoice"
            value={
              nextInvoice?.due_at
                ? new Date(nextInvoice.due_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                  })
                : month
            }
            hint={
              nextInvoice
                ? `${formatMoneyMinor(Number(nextInvoice.total_minor ?? nextInvoice.amount_minor ?? 0), "USD")} scheduled`
                : "No open invoice"
            }
            accent="warning"
            onClick={() => onNavigate("#/invoices")}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <DualLineChart
            title="Usage & spend"
            series={spendSeries}
            emptyLabel="No paid invoices to chart yet."
            legendA="Monthly spend"
            legendB="Usage (est.)"
            yFormatter={(v) => formatMoneyMinor(v, "USD")}
          />

          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="m-0 text-section text-text-primary">Payment status</h3>
              <StatusBadge tone={data.alerts?.payment_due ? "warning" : "success"}>
                {data.alerts?.payment_due ? "Payment due" : "Autopay ready"}
              </StatusBadge>
            </div>
            <p className="m-0 text-body-sm text-text-muted">Primary payment method</p>
            <p className="mt-1 mb-0 text-body font-semibold text-text-primary">
              {defaultMethod
                ? `${defaultMethod.brand || "Card"} ending in ${defaultMethod.last4 || "••••"}`
                : "No payment method on file"}
            </p>
            {defaultMethod?.exp_month && defaultMethod?.exp_year ? (
              <p className="mt-1 mb-0 text-body-sm text-text-muted">
                Expires {String(defaultMethod.exp_month).padStart(2, "0")}/{defaultMethod.exp_year}
              </p>
            ) : null}
            <p className="mt-4 mb-1 text-body-sm text-text-muted">Invoices due</p>
            <p className="m-0 text-page font-bold text-text-primary">
              {formatMoneyMinor(openTotal, "USD")}
            </p>
            <button
              type="button"
              className="mt-4 bg-transparent p-0 text-body font-semibold text-text-brand"
              onClick={() => onNavigate("#/payment-methods")}
            >
              Update payment method →
            </button>
          </article>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h3 className="m-0 text-section text-text-primary">Recent invoices</h3>
              <button
                type="button"
                className="bg-transparent p-0 text-body font-semibold text-text-brand"
                onClick={() => onNavigate("#/invoices")}
              >
                View all invoices →
              </button>
            </div>
            {invoices.length === 0 ? (
              <p className="m-0 py-10 text-center text-body text-text-muted">No invoices yet.</p>
            ) : (
              <div className="overflow-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-label uppercase text-text-muted">
                      <th className="border-0 px-2 py-2">Invoice</th>
                      <th className="border-0 px-2 py-2">Date</th>
                      <th className="border-0 px-2 py-2">Amount</th>
                      <th className="border-0 px-2 py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoices.slice(0, 6).map((invoice) => (
                      <tr key={invoice.id}>
                        <td className="px-2 py-3 font-medium text-text-primary">
                          {invoice.id.slice(0, 8)}
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {invoice.created_at
                            ? new Date(invoice.created_at).toLocaleDateString("en-US", {
                                month: "short",
                                day: "numeric",
                                year: "numeric",
                              })
                            : "—"}
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {formatMoneyMinor(
                            Number(invoice.total_minor ?? invoice.amount_minor ?? 0),
                            invoice.currency ?? "USD",
                          )}
                        </td>
                        <td className="px-2 py-3">
                          <StatusBadge
                            tone={
                              (invoice.status ?? "").toLowerCase() === "paid"
                                ? "success"
                                : "warning"
                            }
                          >
                            {invoice.status || "Open"}
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
            <h3 className="m-0 text-section text-text-primary">Payment methods</h3>
            <div className="mt-4 space-y-3">
              {paymentMethods.length === 0 ? (
                <p className="m-0 text-body text-text-muted">No saved payment methods.</p>
              ) : (
                paymentMethods.slice(0, 3).map((method) => (
                  <div
                    key={method.id}
                    className="flex items-center justify-between gap-3 rounded-xl border border-border-default px-3 py-3"
                  >
                    <div>
                      <p className="m-0 font-semibold text-text-primary">
                        {method.brand || "Card"} ending in {method.last4 || "••••"}
                      </p>
                      <p className="m-0 text-body-sm text-text-muted">
                        {method.is_default ? "Default · " : ""}
                        {method.exp_month && method.exp_year
                          ? `Expires ${String(method.exp_month).padStart(2, "0")}/${method.exp_year}`
                          : "On file"}
                      </p>
                    </div>
                    <ActionButton variant="secondary" onClick={() => onNavigate("#/payment-methods")}>
                      Edit
                    </ActionButton>
                  </div>
                ))
              )}
              <button
                type="button"
                className="w-full rounded-xl border border-dashed border-border-strong bg-transparent px-3 py-3 text-body font-semibold text-text-brand"
                onClick={() => onNavigate("#/payment-methods")}
              >
                + Add payment method
              </button>
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}
