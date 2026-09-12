import { FormEvent, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useAgencyCustomerDetail } from "@/features/customers/hooks/useAgencyCustomerDetail";
import { customersListHref } from "@/features/customers/lib/routes";
import { customerStatusTone } from "@/features/customers/lib/status";
import { CUSTOMER_STATUS_ACTIONS } from "@/features/customers/types";
import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";

type Tab = "overview" | "invite" | "plan" | "status" | "resources";

export function AgencyCustomerDetailScreen({ customerId }: { customerId: string }) {
  const {
    detail,
    planVersions,
    resources,
    error,
    message,
    loading,
    busy,
    setStatus,
    assignPlan,
    inviteCustomerUser,
  } = useAgencyCustomerDetail(customerId);

  const [tab, setTab] = useState<Tab>("overview");
  const [statusReason, setStatusReason] = useState("");
  const [pendingAction, setPendingAction] = useState("");

  async function onAssignPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await assignPlan(String(form.get("plan_version_id") || ""));
  }

  async function onInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await inviteCustomerUser(
        String(form.get("email") || "").trim(),
        String(form.get("role") || "customer_owner"),
      );
      event.currentTarget.reset();
    } catch {
      /* hook message */
    }
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
    { id: "invite", label: "Invite" },
    { id: "plan", label: "Plan" },
    { id: "status", label: "Status" },
    { id: "resources", label: "Resources" },
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

  const hasSubscription = Boolean(detail.subscription?.plan_version_id);

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
            <p className="mt-1 mb-0 text-body text-text-muted">{detail.id}</p>
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
              <InfoTile label="Status" value={detail.status || "—"} />
              <InfoTile label="Owner email" value={detail.owner_email || "—"} />
              <InfoTile label="Legal name" value={detail.legal_name || "—"} />
              <InfoTile label="Phone" value={detail.phone || "—"} />
              <InfoTile label="Country" value={detail.country || "—"} />
              <InfoTile label="Timezone" value={detail.timezone || "—"} />
            </div>
            <ApiNote>
              AG2-003: Profile fields are shown read-only. PATCH profile is not available on the
              agency customer API yet. Service status changes use the Status tab.
            </ApiNote>
          </div>
        ) : null}

        {tab === "invite" ? (
          <div className="grid gap-4">
            <p className="m-0 text-body text-text-secondary">
              Invite customer owner/admin users via agency team (AG2-002).
            </p>
            <form className="grid gap-3 sm:grid-cols-[1.2fr_1fr_auto] sm:items-end" onSubmit={(e) => void onInvite(e)}>
              <FormField label="Email" name="email" type="email" required />
              <FormSelect label="Role" name="role" defaultValue="customer_owner">
                <option value="customer_owner">customer_owner</option>
                <option value="customer_admin">customer_admin</option>
              </FormSelect>
              <ActionButton type="submit" disabled={busy}>
                Send invite
              </ActionButton>
            </form>
          </div>
        ) : null}

        {tab === "plan" ? (
          <div className="grid gap-4">
            {detail.subscription ? (
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <InfoTile label="Plan" value={detail.subscription.plan_name || "—"} />
                <InfoTile
                  label="Version"
                  value={String(detail.subscription.plan_version ?? "—")}
                />
                <InfoTile label="Status" value={detail.subscription.status || "—"} />
              </div>
            ) : (
              <p className="m-0 text-body text-text-muted">
                No subscription on detail payload. First-time assign creates an invoice.
              </p>
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
                Plan change after first assign is not available yet (same gap as platform SA3).
              </ApiNote>
            )}

            <ApiNote>
              GET /agency/customers/{"{id}"}/subscription and usage are not exposed. Remaining
              minutes are not shown here.
            </ApiNote>
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

        {tab === "resources" ? (
          <div className="grid gap-5">
            <ResourceTable
              title="Agents"
              empty="No agents for this customer."
              rows={resources.agents.map((row) => [
                row.display_name || row.id.slice(0, 8),
                row.status || "—",
                row.id.slice(0, 8),
              ])}
              columns={["Name", "Status", "Id"]}
            />
            <ResourceTable
              title="Numbers"
              empty="No numbers linked to this customer."
              rows={resources.numbers.map((row) => [
                row.e164 || row.id.slice(0, 8),
                row.status || "—",
                row.id.slice(0, 8),
              ])}
              columns={["Number", "Status", "Id"]}
            />
            <ResourceTable
              title="Calls"
              empty="No recent calls."
              rows={resources.calls.map((row) => [
                row.id.slice(0, 8),
                row.status || "—",
                String(row.billed_minutes ?? 0),
              ])}
              columns={["Call", "Status", "Minutes"]}
            />
            <ResourceTable
              title="Knowledge"
              empty="No knowledge sources."
              rows={resources.knowledge.map((row) => [
                row.title || row.name || row.id.slice(0, 8),
                row.status || "—",
                row.id.slice(0, 8),
              ])}
              columns={["Source", "Status", "Id"]}
            />
            <ResourceTable
              title="Integrations"
              empty="No integrations."
              rows={resources.integrations.map((row) => [
                row.provider || row.id.slice(0, 8),
                row.status || "—",
                row.id.slice(0, 8),
              ])}
              columns={["Provider", "Status", "Id"]}
            />
            <ResourceTable
              title="Invoices"
              empty="No invoices."
              rows={resources.invoices.map((row) => [
                row.id.slice(0, 8),
                row.status || "—",
                formatMoneyMinor(row.total_minor ?? 0, row.currency || "USD"),
              ])}
              columns={["Invoice", "Status", "Total"]}
            />
            <ApiNote>
              AG2-005 usage/minutes remaining is not available on agency APIs yet. Other resources
              are composed from sibling agency endpoints.
            </ApiNote>
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

function ResourceTable({
  title,
  columns,
  rows,
  empty,
}: {
  title: string;
  columns: string[];
  rows: string[][];
  empty: string;
}) {
  return (
    <div>
      <h3 className="m-0 mb-2 text-section text-text-primary">{title}</h3>
      {rows.length === 0 ? (
        <p className="m-0 text-body text-text-muted">{empty}</p>
      ) : (
        <div className="overflow-auto">
          <table className="min-w-full">
            <thead>
              <tr className="text-label uppercase text-text-muted">
                {columns.map((col) => (
                  <th key={col} className="border-0 px-2 py-2 text-left">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${title}-${index}`}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="px-2 py-3 text-text-secondary">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
