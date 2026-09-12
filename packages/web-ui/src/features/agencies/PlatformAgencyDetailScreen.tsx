import { FormEvent, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { ActionButton } from "@/components/ui/ActionButton";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AgencyField } from "@/features/agencies/components/AgencyField";
import { usePlatformAgencyDetail } from "@/features/agencies/hooks/usePlatformAgencyDetail";
import { agenciesListHref } from "@/features/agencies/lib/routes";
import { agencyStatusTone, bpsToPercent } from "@/features/agencies/lib/status";
import {
  CAPABILITY_FIELDS,
  STATUS_ACTIONS,
  defaultCapabilities,
} from "@/features/agencies/types";
import {
  formatCount,
  formatMoneyMinor,
} from "@/features/dashboard/lib/format";
import { ApiNote } from "@/features/platform/ux/ApiNote";

type Tab =
  | "overview"
  | "profile"
  | "commission"
  | "status"
  | "capabilities"
  | "financial"
  | "resources"
  | "notes";

export function PlatformAgencyDetailScreen({ agencyId }: { agencyId: string }) {
  const {
    detail,
    wallet,
    dashboard,
    payouts,
    customers,
    agents,
    numbers,
    calls,
    integrations,
    notes,
    error,
    message,
    loading,
    busy,
    saveProfile,
    setCommission,
    setStatus,
    setCapabilities,
    addNote,
  } = usePlatformAgencyDetail(agencyId);

  const [tab, setTab] = useState<Tab>("overview");

  async function onProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await saveProfile({
      display_name: String(form.get("display_name") || ""),
      legal_name: String(form.get("legal_name") || ""),
    });
  }

  async function onCommission(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await setCommission(Number(form.get("commission_rate_bps") || 0));
  }

  async function onCapabilities(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail?.capabilities) return;
    const form = new FormData(event.currentTarget);
    const next = { ...defaultCapabilities() };
    for (const field of CAPABILITY_FIELDS) {
      next[field.key] = form.get(field.key) === "on";
    }
    await setCapabilities(next);
  }

  async function onNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await addNote({
      body: String(form.get("body") || ""),
      risk_flag: form.get("risk_flag") === "on",
    });
    event.currentTarget.reset();
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "overview", label: "Overview" },
    { id: "profile", label: "Profile" },
    { id: "commission", label: "Commission" },
    { id: "status", label: "Status" },
    { id: "capabilities", label: "Capabilities" },
    { id: "financial", label: "Financial" },
    { id: "resources", label: "Resources" },
    { id: "notes", label: "Notes" },
  ];

  const currency = detail?.currency || dashboard?.currency || wallet?.currency || "USD";
  const gross = Number(dashboard?.financial?.gross_revenue_minor ?? 0);
  const commissionMrr = Number(dashboard?.financial?.agency_commission_minor ?? 0);

  if (loading) {
    return (
      <section className="mx-auto max-w-[1200px]">
        <p className="m-0 text-body text-text-muted" role="status">
          Loading agency…
        </p>
      </section>
    );
  }

  if (error || !detail) {
    return (
      <section className="mx-auto max-w-[1200px]">
        <Link
          to={agenciesListHref()}
          className="mb-3 inline-flex items-center gap-2 text-body font-semibold text-text-secondary no-underline hover:text-text-primary"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Back to agencies
        </Link>
        <p className="text-danger" role="alert">
          {error || "Agency not found."}
        </p>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6">
        <Link
          to={agenciesListHref()}
          className="mb-3 inline-flex items-center gap-2 text-body font-semibold text-text-secondary no-underline hover:text-text-primary"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Back to agencies
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
              {detail.display_name || detail.id.slice(0, 8)}
            </h1>
            <p className="mt-1 mb-0 text-body text-text-muted">
              {detail.legal_name || "—"} · {detail.id}
            </p>
          </div>
          <StatusBadge tone={agencyStatusTone(detail.status)}>
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
              <InfoTile label="Agency status" value={detail.status || "—"} />
              <InfoTile label="Tenant status" value={detail.tenant_status || "—"} />
              <InfoTile label="Commission" value={bpsToPercent(detail.commission_rate_bps)} />
              <InfoTile label="Currency" value={detail.currency || "USD"} />
              <InfoTile label="DB name" value={detail.database?.name || "—"} />
              <InfoTile label="DB username" value={detail.database?.username || "—"} />
              <InfoTile
                label="DB host"
                value={
                  detail.database
                    ? `${detail.database.host || "—"}:${detail.database.port ?? "—"}`
                    : "—"
                }
              />
              <InfoTile label="DB health" value={detail.database?.status || "—"} />
              <InfoTile label="Schema" value={detail.database?.schema_version || "—"} />
            </div>
            <ApiNote>
              MySQL password is never returned by the API. Database name is server-allocated and
              cannot be changed from this screen.
            </ApiNote>
          </div>
        ) : null}

        {tab === "profile" ? (
          <div className="grid gap-4">
            <form className="grid gap-3 sm:grid-cols-2" onSubmit={(e) => void onProfile(e)}>
              <AgencyField
                label="Display name"
                name="display_name"
                defaultValue={detail.display_name || ""}
                required
              />
              <AgencyField
                label="Legal name"
                name="legal_name"
                defaultValue={detail.legal_name || ""}
                required
              />
              <div className="sm:col-span-2">
                <ActionButton type="submit" disabled={busy}>
                  Save profile
                </ActionButton>
              </div>
            </form>
            <ApiNote>
              Extended legal/operating fields beyond display and legal name are not exposed by the
              current API payload.
            </ApiNote>
          </div>
        ) : null}

        {tab === "commission" ? (
          <div className="grid gap-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <InfoTile label="Current rate" value={bpsToPercent(detail.commission_rate_bps)} />
              <InfoTile
                label="Effective at"
                value={
                  detail.rate_effective_at
                    ? new Date(detail.rate_effective_at).toLocaleString()
                    : "—"
                }
              />
            </div>
            <form
              className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end"
              onSubmit={(e) => void onCommission(e)}
            >
              <AgencyField
                label="New commission (bps)"
                name="commission_rate_bps"
                type="number"
                defaultValue={String(detail.commission_rate_bps ?? 1500)}
                required
              />
              <ActionButton type="submit" disabled={busy}>
                Update commission
              </ActionButton>
            </form>
            <ApiNote>
              The API sets effective time to now; a custom future effective date field is not
              accepted yet. Historical ledger entries retain their original rate snapshot.
            </ApiNote>
          </div>
        ) : null}

        {tab === "status" ? (
          <div className="grid gap-4">
            <p className="m-0 text-body text-text-secondary">
              Current status: <strong>{detail.status || "unknown"}</strong> · Tenant DB:{" "}
              <strong>{detail.tenant_status || "—"}</strong>
            </p>
            <div className="flex flex-wrap gap-2">
              {STATUS_ACTIONS.map((item) => (
                <ActionButton
                  key={item.action}
                  variant={
                    item.action === "close" || item.action === "suspend" ? "outline" : "secondary"
                  }
                  disabled={busy}
                  onClick={() => void setStatus(item.action)}
                >
                  {item.label}
                </ActionButton>
              ))}
            </div>
          </div>
        ) : null}

        {tab === "capabilities" ? (
          <div className="grid gap-4">
            <form className="grid gap-3" onSubmit={(e) => void onCapabilities(e)}>
              <div className="grid gap-2 sm:grid-cols-2">
                {CAPABILITY_FIELDS.map((field) => (
                  <label key={field.key} className="m-0 flex items-center gap-2 font-normal">
                    <input
                      type="checkbox"
                      name={field.key}
                      defaultChecked={Boolean(detail.capabilities?.[field.key])}
                    />
                    <span className="text-body text-text-secondary">{field.label}</span>
                  </label>
                ))}
              </div>
              <div>
                <ActionButton type="submit" disabled={busy}>
                  Save capabilities
                </ActionButton>
              </div>
            </form>
          </div>
        ) : null}

        {tab === "financial" ? (
          <div className="grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              <MetricCard
                label="Customer revenue (period)"
                value={formatMoneyMinor(gross, currency)}
                hint="From platform dashboard?agency_id"
                accent="brand"
              />
              <MetricCard
                label="Commission earned (period)"
                value={formatMoneyMinor(commissionMrr, currency)}
                hint="Agency commission in selected period"
                accent="success"
              />
              <MetricCard
                label="Available wallet"
                value={formatMoneyMinor(Number(wallet?.available_minor ?? 0), currency)}
                hint="Current available commission"
                accent="info"
              />
              <MetricCard
                label="Held"
                value={formatMoneyMinor(Number(wallet?.on_hold_minor ?? 0), currency)}
                hint="Hold window funds"
                accent="warning"
              />
              <MetricCard
                label="Pending withdrawal"
                value={formatMoneyMinor(Number(wallet?.withdrawal_pending_minor ?? 0), currency)}
                hint="Reserved for payout"
                accent="muted"
              />
              <MetricCard
                label="Lifetime paid"
                value={formatMoneyMinor(Number(wallet?.lifetime_paid_minor ?? 0), currency)}
                hint="Paid payouts total"
                accent="muted"
              />
            </div>

            <div>
              <h3 className="m-0 mb-2 text-section text-text-primary">Payout history</h3>
              {payouts.length === 0 ? (
                <p className="m-0 text-body text-text-muted">No payouts for this agency.</p>
              ) : (
                <div className="overflow-auto">
                  <table className="min-w-full">
                    <thead>
                      <tr className="text-label uppercase text-text-muted">
                        <th className="border-0 px-2 py-2 text-left">Status</th>
                        <th className="border-0 px-2 py-2 text-left">Amount</th>
                        <th className="border-0 px-2 py-2 text-left">Paid at</th>
                        <th className="border-0 px-2 py-2 text-left">Id</th>
                      </tr>
                    </thead>
                    <tbody>
                      {payouts.slice(0, 10).map((row) => (
                        <tr key={String(row.id)}>
                          <td className="px-2 py-3">
                            <StatusBadge tone={agencyStatusTone(String(row.status))}>
                              {String(row.status || "—")}
                            </StatusBadge>
                          </td>
                          <td className="px-2 py-3 text-text-secondary">
                            {formatMoneyMinor(
                              Number(row.amount_minor ?? 0),
                              String(row.currency || currency),
                            )}
                          </td>
                          <td className="px-2 py-3 text-text-secondary">
                            {row.paid_at ? String(row.paid_at) : "—"}
                          </td>
                          <td className="px-2 py-3 text-text-muted">
                            {String(row.id).slice(0, 8)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : null}

        {tab === "resources" ? (
          <div className="grid gap-4">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <InfoTile label="Customers" value={formatCount(customers.length)} />
              <InfoTile label="Agents" value={formatCount(agents.length)} />
              <InfoTile label="Numbers" value={formatCount(numbers.length)} />
              <InfoTile label="Calls" value={formatCount(calls.length)} />
              <InfoTile label="Integrations" value={formatCount(integrations.length)} />
            </div>
            <ResourceTable
              title="Customers"
              rows={customers}
              columns={[
                { key: "display_name", label: "Name" },
                { key: "status", label: "Status" },
                { key: "id", label: "Id" },
              ]}
            />
            <ResourceTable
              title="Agents"
              rows={agents}
              columns={[
                { key: "display_name", label: "Name" },
                { key: "status", label: "Status" },
                { key: "agent_type", label: "Type" },
                { key: "id", label: "Id" },
              ]}
            />
            <ResourceTable
              title="Numbers"
              rows={numbers}
              columns={[
                { key: "e164", label: "Number" },
                { key: "status", label: "Status" },
                { key: "assigned_agent_id", label: "Agent" },
              ]}
            />
            <ApiNote>
              Resource lists are filtered client-side from platform collection APIs. A dedicated
              agency team directory and agency-scoped knowledge index for Super Admin are not
              available yet.
            </ApiNote>
          </div>
        ) : null}

        {tab === "notes" ? (
          <div className="grid gap-4">
            <form className="grid gap-3" onSubmit={(e) => void onNote(e)}>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Internal note</span>
                <textarea
                  name="body"
                  required
                  rows={4}
                  maxLength={2000}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                />
              </label>
              <label className="m-0 flex items-center gap-2 font-normal">
                <input type="checkbox" name="risk_flag" />
                <span className="text-body text-text-secondary">Mark as risk flag</span>
              </label>
              <div>
                <ActionButton type="submit" disabled={busy}>
                  Add note
                </ActionButton>
              </div>
            </form>
            {notes.length === 0 ? (
              <p className="m-0 text-body text-text-muted">No internal notes yet.</p>
            ) : (
              <ul className="m-0 grid list-none gap-3 p-0">
                {notes.map((note) => (
                  <li
                    key={note.id}
                    className="rounded-xl border border-border-default bg-canvas px-3 py-3"
                  >
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      {note.risk_flag ? (
                        <StatusBadge tone="danger">Risk</StatusBadge>
                      ) : (
                        <StatusBadge tone="neutral">Note</StatusBadge>
                      )}
                      <span className="text-body-sm text-text-muted">
                        {note.created_at ? new Date(note.created_at).toLocaleString() : "—"}
                      </span>
                    </div>
                    <p className="m-0 whitespace-pre-wrap text-body text-text-secondary">
                      {note.body}
                    </p>
                  </li>
                ))}
              </ul>
            )}
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
  rows,
  columns,
}: {
  title: string;
  rows: Record<string, unknown>[];
  columns: Array<{ key: string; label: string }>;
}) {
  return (
    <div>
      <h3 className="m-0 mb-2 text-section text-text-primary">
        {title}
        <span className="ml-2 text-body font-normal text-text-muted">({rows.length})</span>
      </h3>
      {rows.length === 0 ? (
        <p className="m-0 text-body text-text-muted">No {title.toLowerCase()} for this agency.</p>
      ) : (
        <div className="overflow-auto">
          <table className="min-w-full">
            <thead>
              <tr className="text-label uppercase text-text-muted">
                {columns.map((col) => (
                  <th key={col.key} className="border-0 px-2 py-2 text-left">
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 8).map((row, index) => (
                <tr key={String(row.id ?? index)}>
                  {columns.map((col) => (
                    <td key={col.key} className="px-2 py-3 text-text-secondary">
                      {col.key === "status" ? (
                        <StatusBadge tone={agencyStatusTone(String(row[col.key] ?? ""))}>
                          {String(row[col.key] ?? "—")}
                        </StatusBadge>
                      ) : (
                        String(row[col.key] ?? "—").slice(0, 40)
                      )}
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
