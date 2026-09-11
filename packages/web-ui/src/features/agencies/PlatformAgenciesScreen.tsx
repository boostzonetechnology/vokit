import { FormEvent, useMemo, useState, type ReactNode } from "react";

import { ActionButton } from "../../components/ui/ActionButton";
import { MetricCard } from "../../components/ui/MetricCard";
import { StatusBadge, type BadgeTone } from "../../components/ui/StatusBadge";
import {
  formatCount,
  formatMoneyMinor,
} from "../dashboard/lib/format";
import { usePlatformAgencies } from "./hooks/usePlatformAgencies";
import {
  CAPABILITY_FIELDS,
  STATUS_ACTIONS,
  defaultCapabilities,
  type AgencyCapabilities,
} from "./types";

type Tab =
  | "profile"
  | "commission"
  | "status"
  | "capabilities"
  | "financial"
  | "resources"
  | "notes";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "restricted" || value === "pending" || value === "under_review") return "warning";
  if (value === "suspended" || value === "closed") return "danger";
  return "neutral";
}

function ApiNote({ children }: { children: ReactNode }) {
  return (
    <p className="m-0 rounded-lg border border-dashed border-border-strong bg-canvas px-3 py-2 text-body-sm text-text-muted">
      {children}
    </p>
  );
}

function bpsToPercent(bps?: number): string {
  if (typeof bps !== "number") return "—";
  return `${(bps / 100).toFixed(2)}%`;
}

export function PlatformAgenciesScreen() {
  const {
    agencies,
    selectedId,
    setSelectedId,
    detail,
    wallet,
    dashboard,
    payouts,
    customers,
    agents,
    numbers,
    calls,
    integrations,
    error,
    message,
    loading,
    busy,
    createAgency,
    saveProfile,
    setCommission,
    setStatus,
    setCapabilities,
  } = usePlatformAgencies();

  const [tab, setTab] = useState<Tab>("profile");
  const [showCreate, setShowCreate] = useState(false);
  const [query, setQuery] = useState("");
  const [createCaps, setCreateCaps] = useState<AgencyCapabilities>(defaultCapabilities());

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return agencies;
    return agencies.filter((row) =>
      [row.display_name, row.legal_name, row.status, row.id, row.currency]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [agencies, query]);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createAgency({
        display_name: String(form.get("display_name") || ""),
        legal_name: String(form.get("legal_name") || ""),
        owner_email: String(form.get("owner_email") || ""),
        commission_rate_bps: Number(form.get("commission_rate_bps") || 0),
        currency: String(form.get("currency") || "USD"),
        capabilities: createCaps,
      });
      setShowCreate(false);
      event.currentTarget.reset();
      setCreateCaps(defaultCapabilities());
      setTab("profile");
    } catch {
      /* message in hook */
    }
  }

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

  const tabs: Array<{ id: Tab; label: string }> = [
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

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Agencies
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA2-001–008 · Permissions: agencies.view / create / manage · commission.edit ·
            billing.view
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="m-0 font-normal">
            <span className="sr-only">Search agencies</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search agencies…"
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close form" : "Create agency"}
          </ActionButton>
        </div>
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

      {showCreate ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 text-section text-text-primary">Create agency</h2>
          <p className="mt-1 mb-4 text-body-sm text-text-muted">
            Creates the agency, owner invitation, commission, currency, and initial capability
            restrictions. Tenant database credentials are never collected in the browser.
          </p>
          <form className="grid gap-3" onSubmit={(event) => void onCreate(event)}>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <Field label="Display name" name="display_name" required />
              <Field label="Legal name" name="legal_name" required />
              <Field label="Owner email" name="owner_email" type="email" required />
              <Field
                label="Commission (bps)"
                name="commission_rate_bps"
                type="number"
                defaultValue="1500"
              />
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Currency</span>
                <select
                  name="currency"
                  defaultValue="USD"
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  <option value="USD">USD</option>
                </select>
              </label>
            </div>
            <div>
              <p className="mb-2 mt-1 text-body-sm font-semibold text-text-primary">
                Initial restrictions
              </p>
              <div className="grid gap-2 sm:grid-cols-2">
                {CAPABILITY_FIELDS.map((field) => (
                  <label key={field.key} className="m-0 flex items-center gap-2 font-normal">
                    <input
                      type="checkbox"
                      checked={createCaps[field.key]}
                      onChange={(event) =>
                        setCreateCaps((prev) => ({
                          ...prev,
                          [field.key]: event.target.checked,
                        }))
                      }
                    />
                    <span className="text-body text-text-secondary">{field.label}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <ActionButton type="submit" disabled={busy}>
                Create agency
              </ActionButton>
            </div>
          </form>
        </article>
      ) : null}

      <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <h2 className="m-0 mb-3 text-section text-text-primary">
          Agency directory
          <span className="ml-2 text-body font-normal text-text-muted">({filtered.length})</span>
        </h2>
        {loading ? (
          <p className="m-0 text-body text-text-muted">Loading agencies…</p>
        ) : filtered.length === 0 ? (
          <p className="m-0 py-10 text-center text-body text-text-muted">No agencies yet.</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Agency</th>
                  <th className="border-0 px-2 py-2 text-left">Legal</th>
                  <th className="border-0 px-2 py-2 text-left">Status</th>
                  <th className="border-0 px-2 py-2 text-left">Tenant DB</th>
                  <th className="border-0 px-2 py-2 text-left">Commission</th>
                  <th className="border-0 px-2 py-2 text-left">Currency</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr
                    key={row.id}
                    className={
                      selectedId === row.id
                        ? "cursor-pointer bg-brand-subtle/40"
                        : "cursor-pointer hover:bg-canvas"
                    }
                    onClick={() => {
                      setSelectedId(row.id);
                      setTab("profile");
                    }}
                  >
                    <td className="px-2 py-3 font-semibold text-text-primary">
                      {row.display_name || row.id.slice(0, 8)}
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{row.legal_name || "—"}</td>
                    <td className="px-2 py-3">
                      <StatusBadge tone={statusTone(row.status)}>
                        {row.status || "unknown"}
                      </StatusBadge>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{row.tenant_status || "—"}</td>
                    <td className="px-2 py-3 text-text-secondary">
                      {bpsToPercent(row.commission_rate_bps)}
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{row.currency || "USD"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      {detail ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="m-0 text-section text-text-primary">
                {detail.display_name || detail.id.slice(0, 8)}
              </h2>
              <p className="mt-1 mb-0 text-body text-text-muted">
                {detail.legal_name || "—"} · {detail.id}
              </p>
            </div>
            <StatusBadge tone={statusTone(detail.status)}>
              {detail.status || "unknown"}
            </StatusBadge>
          </div>

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

          {tab === "profile" ? (
            <div className="grid gap-4">
              <form className="grid gap-3 sm:grid-cols-2" onSubmit={(e) => void onProfile(e)}>
                <Field
                  label="Display name"
                  name="display_name"
                  defaultValue={detail.display_name || ""}
                  required
                />
                <Field
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
                Profile updates use PATCH /api/v1/platform/agencies/{"{id}"} (agencies.manage).
                Extended legal/operating fields beyond display and legal name are not exposed by
                the current API payload.
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
              <form className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end" onSubmit={(e) => void onCommission(e)}>
                <Field
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
                Commission changes use POST /api/v1/platform/agencies/{"{id}"}/commission
                (commission.edit). The API sets effective time to now; a custom future effective
                date field is not accepted yet. Historical ledger entries retain their original
                rate snapshot.
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
                    variant={item.action === "close" || item.action === "suspend" ? "outline" : "secondary"}
                    disabled={busy}
                    onClick={() => void setStatus(item.action)}
                  >
                    {item.label}
                  </ActionButton>
                ))}
              </div>
              <ApiNote>
                Status control uses POST /api/v1/platform/agencies/{"{id}"}/status with action:
                activate, restrict, review, suspend, or close. Reactivate is accepted as activate.
              </ApiNote>
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
              <ApiNote>
                Capability overrides use POST /api/v1/platform/agencies/{"{id}"}/capabilities
                (agencies.manage).
              </ApiNote>
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
                  value={formatMoneyMinor(
                    Number(wallet?.withdrawal_pending_minor ?? 0),
                    currency,
                  )}
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
                              <StatusBadge tone={statusTone(String(row.status))}>
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

              {!wallet ? (
                <ApiNote>
                  Wallet data requires GET /api/v1/platform/agencies/{"{id}"}/wallet
                  (billing.view). If this section is empty, the request failed or returned no
                  buckets.
                </ApiNote>
              ) : null}
              <ApiNote>
                Dedicated commission-MRR and recurring MRR series are approximated from the
                agency-scoped dashboard financial/KPI payload for the last 30 days.
              </ApiNote>
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
                <InfoTile label="Knowledge" value="—" />
                <InfoTile label="Team" value="—" />
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
                Resource lists are filtered client-side from platform collection APIs
                (customers, agents, phone-numbers, calls, integrations). A dedicated agency team
                directory and agency-scoped knowledge index for Super Admin are not available yet.
              </ApiNote>
            </div>
          ) : null}

          {tab === "notes" ? (
            <div className="grid gap-4">
              <ApiNote>
                Internal notes and risk flags (SA2-008) are not available yet. There is currently
                no platform API to create, list, or update agency-only notes or risk flags.
              </ApiNote>
              <ActionButton disabled title="API not available yet">
                Add internal note
              </ActionButton>
            </div>
          ) : null}
        </article>
      ) : (
        <p className="text-body text-text-muted">Select an agency to manage SA2 controls.</p>
      )}
    </section>
  );
}

function Field({
  label,
  name,
  type = "text",
  defaultValue,
  required,
}: {
  label: string;
  name: string;
  type?: string;
  defaultValue?: string;
  required?: boolean;
}) {
  return (
    <label className="m-0 grid gap-1.5 font-normal">
      <span className="text-body-sm text-text-muted">{label}</span>
      <input
        name={name}
        type={type}
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
      <p className="mt-1 mb-0 font-semibold text-text-primary">{value}</p>
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
                        <StatusBadge tone={statusTone(String(row[col.key] ?? ""))}>
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
