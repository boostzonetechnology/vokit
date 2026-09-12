import { FormEvent, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePlatformCustomerDetail } from "@/features/customers/hooks/usePlatformCustomerDetail";
import { customersListHref } from "@/features/customers/lib/routes";
import { customerStatusTone } from "@/features/customers/lib/status";
import { CUSTOMER_STATUS_ACTIONS } from "@/features/customers/types";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";

type Tab = "overview" | "minutes" | "plan" | "status";

export function PlatformCustomerDetailScreen({ customerId }: { customerId: string }) {
  const {
    detail,
    usage,
    planVersions,
    agencyLabel,
    error,
    message,
    loading,
    busy,
    setStatus,
    assignPlan,
    adjustMinutes,
  } = usePlatformCustomerDetail(customerId);

  const [tab, setTab] = useState<Tab>("overview");
  const [statusReason, setStatusReason] = useState("");
  const [pendingAction, setPendingAction] = useState("");

  async function onAssignPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await assignPlan(String(form.get("plan_version_id") || ""));
  }

  async function onAdjustMinutes(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const minutes = Number(form.get("minutes") || 0);
    const reason = String(form.get("reason") || "").trim();
    await adjustMinutes(minutes, reason);
    event.currentTarget.reset();
  }

  async function onConfirmStatus() {
    if (!pendingAction) return;
    const needsReason = CUSTOMER_STATUS_ACTIONS.find((row) => row.action === pendingAction)
      ?.needsReason;
    if (needsReason && !statusReason.trim()) return;
    await setStatus(pendingAction, statusReason.trim());
    setPendingAction("");
    setStatusReason("");
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "overview", label: "Overview" },
    { id: "minutes", label: "Minutes" },
    { id: "plan", label: "Plan" },
    { id: "status", label: "Status" },
  ];

  if (loading) {
    return (
      <section className="mx-auto max-w-[1200px]">
        <p className="m-0 text-body text-text-muted" role="status">
          Loading customer…
        </p>
      </section>
    );
  }

  if (error || !detail) {
    return (
      <section className="mx-auto max-w-[1200px]">
        <Link
          to={customersListHref()}
          className="mb-3 inline-flex items-center gap-2 text-body font-semibold text-text-secondary no-underline hover:text-text-primary"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Back to customers
        </Link>
        <p className="text-danger" role="alert">
          {error || "Customer not found."}
        </p>
      </section>
    );
  }

  const remaining =
    usage?.remaining_minutes ?? detail.remaining_minutes ?? 0;
  const subscription = detail.subscription;
  const hasSubscription = Boolean(subscription?.plan_version_id);

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6">
        <Link
          to={customersListHref()}
          className="mb-3 inline-flex items-center gap-2 text-body font-semibold text-text-secondary no-underline hover:text-text-primary"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Back to customers
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
              {detail.display_name || detail.id.slice(0, 8)}
            </h1>
            <p className="mt-1 mb-0 text-body text-text-muted">
              {agencyLabel} · {detail.id}
            </p>
          </div>
          <StatusBadge tone={customerStatusTone(detail.status)}>
            {detail.status || "unknown"}
          </StatusBadge>
        </div>
      </div>

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

      <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        {tab === "overview" ? (
          <div className="grid gap-4">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <InfoTile label="Agency" value={agencyLabel} />
              <InfoTile label="Status" value={detail.status || "—"} />
              <InfoTile label="Owner email" value={detail.owner_email || "—"} />
              <InfoTile label="Legal name" value={detail.legal_name || "—"} />
              <InfoTile label="Phone" value={detail.phone || "—"} />
              <InfoTile label="Country" value={detail.country || "—"} />
              <InfoTile label="Timezone" value={detail.timezone || "—"} />
              <InfoTile label="Remaining minutes" value={String(remaining)} />
              <InfoTile
                label="Plan"
                value={
                  subscription
                    ? `${subscription.plan_name || "Plan"} v${subscription.plan_version ?? "—"}`
                    : "None"
                }
              />
            </div>
          </div>
        ) : null}

        {tab === "minutes" ? (
          <div className="grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <MetricCard
                label="Remaining minutes"
                value={String(remaining)}
                hint="Minute lots (Q-003)"
                accent="brand"
              />
              <MetricCard
                label="Active lots"
                value={String(usage?.lots?.length ?? 0)}
                hint="Usage lot count"
                accent="muted"
              />
            </div>

            <form className="grid gap-3 sm:grid-cols-2" onSubmit={(e) => void onAdjustMinutes(e)}>
              <FormField
                label="Minutes (+ credit / − debit)"
                name="minutes"
                type="number"
                required
              />
              <FormField label="Reason" name="reason" required />
              <div className="sm:col-span-2">
                <ActionButton type="submit" disabled={busy}>
                  Apply adjustment
                </ActionButton>
              </div>
            </form>

            {(usage?.lots?.length ?? 0) > 0 ? (
              <div className="overflow-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-label uppercase text-text-muted">
                      <th className="border-0 px-2 py-2 text-left">Kind</th>
                      <th className="border-0 px-2 py-2 text-left">Granted</th>
                      <th className="border-0 px-2 py-2 text-left">Remaining</th>
                      <th className="border-0 px-2 py-2 text-left">Id</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(usage?.lots ?? []).map((lot) => (
                      <tr key={lot.id}>
                        <td className="px-2 py-3 text-text-secondary">{lot.kind || "—"}</td>
                        <td className="px-2 py-3 text-text-secondary">
                          {lot.granted_minutes ?? 0}
                        </td>
                        <td className="px-2 py-3 text-text-secondary">
                          {lot.remaining_minutes ?? 0}
                        </td>
                        <td className="px-2 py-3 text-text-muted">{lot.id.slice(0, 8)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="m-0 text-body text-text-muted">No minute lots yet.</p>
            )}
          </div>
        ) : null}

        {tab === "plan" ? (
          <div className="grid gap-4">
            {subscription ? (
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <InfoTile label="Plan" value={subscription.plan_name || "—"} />
                <InfoTile label="Version" value={String(subscription.plan_version ?? "—")} />
                <InfoTile label="Status" value={subscription.status || "—"} />
                <InfoTile
                  label="Included minutes"
                  value={String(subscription.included_minutes ?? "—")}
                />
              </div>
            ) : (
              <p className="m-0 text-body text-text-muted">No active subscription.</p>
            )}

            {!hasSubscription ? (
              <form
                className="grid gap-3 sm:grid-cols-[1.4fr_auto] sm:items-end"
                onSubmit={(e) => void onAssignPlan(e)}
              >
                <FormSelect label="Plan version" name="plan_version_id" required defaultValue="">
                  <option value="" disabled>
                    Select plan version
                  </option>
                  {planVersions.map((row) => (
                    <option key={row.id} value={row.id}>
                      {row.plan_name} v{row.version} ·{" "}
                      {formatMoneyMinor(row.price_minor ?? 0, row.currency || "USD")} ·{" "}
                      {row.included_minutes ?? 0} min
                    </option>
                  ))}
                </FormSelect>
                <ActionButton type="submit" disabled={busy || planVersions.length === 0}>
                  Assign plan
                </ActionButton>
              </form>
            ) : (
              <ApiNote>
                Plan change / version switch is not available yet. First-time assign only.
              </ApiNote>
            )}

            {planVersions.length === 0 && !hasSubscription ? (
              <ApiNote>
                No plan versions loaded. Check plans.manage permission and published plans.
              </ApiNote>
            ) : null}
          </div>
        ) : null}

        {tab === "status" ? (
          <div className="grid gap-4">
            <p className="m-0 text-body text-text-secondary">
              Current status: <strong>{detail.status || "unknown"}</strong>
            </p>
            <div className="flex flex-wrap gap-2">
              {CUSTOMER_STATUS_ACTIONS.map((item) => (
                <ActionButton
                  key={item.action}
                  variant={item.needsReason ? "outline" : "secondary"}
                  disabled={busy}
                  onClick={() => {
                    setPendingAction(item.action);
                    setStatusReason("");
                  }}
                >
                  {item.label}
                </ActionButton>
              ))}
            </div>

            {pendingAction ? (
              <div className="grid gap-3 rounded-xl border border-border-default bg-canvas p-4">
                <p className="m-0 text-body font-semibold text-text-primary">
                  Confirm: {pendingAction}
                </p>
                {CUSTOMER_STATUS_ACTIONS.find((row) => row.action === pendingAction)
                  ?.needsReason ? (
                  <FormField
                    label="Reason"
                    name="reason"
                    required
                    value={statusReason}
                    onChange={(event) => setStatusReason(event.target.value)}
                  />
                ) : null}
                <div className="flex flex-wrap gap-2">
                  <ActionButton
                    disabled={
                      busy ||
                      (Boolean(
                        CUSTOMER_STATUS_ACTIONS.find((row) => row.action === pendingAction)
                          ?.needsReason,
                      ) && !statusReason.trim())
                    }
                    onClick={() => void onConfirmStatus()}
                  >
                    Confirm
                  </ActionButton>
                  <ActionButton
                    variant="outline"
                    disabled={busy}
                    onClick={() => {
                      setPendingAction("");
                      setStatusReason("");
                    }}
                  >
                    Cancel
                  </ActionButton>
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </article>
    </section>
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
