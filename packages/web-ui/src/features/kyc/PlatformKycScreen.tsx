import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformKyc } from "./hooks/usePlatformKyc";
import { DECISION_STATUSES, KYC_STATUSES } from "./types";

type Tab = "queue" | "evidence" | "decision" | "payout" | "refresh" | "settings";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "verified") return "success";
  if (value === "rejected" || value === "suspended" || value === "expired") return "danger";
  if (
    value === "submitted" ||
    value === "under_review" ||
    value === "more_information_required" ||
    value === "incomplete"
  ) {
    return "warning";
  }
  return "neutral";
}

function payoutEligible(status?: string, frozen?: boolean): boolean {
  return status === "verified" && !frozen;
}

export function PlatformKycScreen() {
  const {
    cases,
    agencies,
    settings,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    agencyFilter,
    setAgencyFilter,
    frozenOnly,
    setFrozenOnly,
    agencyName,
    reload,
    overrideCase,
    saveSettings,
  } = usePlatformKyc();

  const [tab, setTab] = useState<Tab>("queue");
  const [note, setNote] = useState("");
  const [decisionStatus, setDecisionStatus] = useState("verified");

  async function onDecision(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    try {
      await overrideCase({
        caseId: selected.id,
        action: "set_status",
        status: decisionStatus,
        internal_note: note || `Decision: ${decisionStatus}`,
      });
      setNote("");
    } catch {
      /* message in hook */
    }
  }

  async function onFreeze(freeze: boolean) {
    if (!selected) return;
    try {
      await overrideCase({
        caseId: selected.id,
        action: freeze ? "freeze" : "unfreeze",
        internal_note: note || (freeze ? "Freeze payouts" : "Unfreeze payouts"),
      });
      setNote("");
    } catch {
      /* message in hook */
    }
  }

  async function onSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await saveSettings({
        provider_slug: String(form.get("provider_slug") || ""),
        api_key_ref: String(form.get("api_key_ref") || ""),
        webhook_secret_ref: String(form.get("webhook_secret_ref") || ""),
        hosted_base_url: String(form.get("hosted_base_url") || ""),
      });
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "queue", label: "Review queue" },
    { id: "evidence", label: "Evidence" },
    { id: "decision", label: "Decision" },
    { id: "payout", label: "Payout gating" },
    { id: "refresh", label: "Refresh" },
    { id: "settings", label: "Provider settings" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            KYC management
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA4-001–005 · Permission: kyc.review
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

      {tab !== "settings" ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Search</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Case, inquiry, agency…"
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
                {KYC_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Agency</span>
              <select
                value={agencyFilter}
                onChange={(event) => setAgencyFilter(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="">All</option>
                {agencies.map((agency) => (
                  <option key={agency.id} value={agency.id}>
                    {agency.display_name || agency.id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </label>
            <label className="m-0 flex items-end gap-2 pb-2 font-normal">
              <input
                type="checkbox"
                checked={frozenOnly}
                onChange={(event) => setFrozenOnly(event.target.checked)}
              />
              <span className="text-body text-text-secondary">Frozen only</span>
            </label>
          </div>
          <ApiNote>
            Server filter supports status. Agency and frozen filters run client-side. Age, country,
            and risk-flag query params are not exposed on GET /api/v1/platform/kyc/cases yet.
          </ApiNote>

          <h2 className="mb-3 mt-4 text-section text-text-primary">
            Cases
            <span className="ml-2 text-body font-normal text-text-muted">({cases.length})</span>
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading KYC cases…</p>
          ) : cases.length === 0 ? (
            <p className="m-0 py-8 text-center text-body text-text-muted">No KYC cases found.</p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Agency</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">Frozen</th>
                    <th className="border-0 px-2 py-2 text-left">Reason</th>
                    <th className="border-0 px-2 py-2 text-left">Case</th>
                  </tr>
                </thead>
                <tbody>
                  {cases.map((row) => (
                    <tr
                      key={row.id}
                      className={
                        selectedId === row.id
                          ? "cursor-pointer bg-brand-subtle/40"
                          : "cursor-pointer hover:bg-canvas"
                      }
                      onClick={() => {
                        setSelectedId(row.id);
                        if (tab === "queue") setTab("evidence");
                      }}
                    >
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {agencyName(row.agency_id)}
                      </td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.frozen ? "Yes" : "No"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.reason_code || "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.id.slice(0, 8)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      ) : null}

      {tab === "evidence" && selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Evidence review</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <InfoTile label="Agency" value={agencyName(selected.agency_id)} />
            <InfoTile label="Status" value={selected.status || "—"} />
            <InfoTile label="Session id" value={selected.session_id || "—"} />
            <InfoTile label="Inquiry id" value={selected.inquiry_id || "—"} />
            <InfoTile label="Last event id" value={selected.last_event_id || "—"} />
            <InfoTile label="Reason code" value={selected.reason_code || "—"} />
            <InfoTile label="External note" value={selected.external_note || "—"} />
            <InfoTile label="Internal note" value={selected.internal_note || "—"} />
          </div>
          <div className="mt-4">
            <ApiNote>
              SA4-002: Vokit does not store KYC document binaries. Evidence is reviewed via the
              external provider inquiry (inquiry_id / session_id). Platform API returns privileged
              case metadata only — no document download route.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "decision" && selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">
            Decision · {agencyName(selected.agency_id)}
          </h2>
          <form className="grid max-w-lg gap-3" onSubmit={(event) => void onDecision(event)}>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Decision</span>
              <select
                value={decisionStatus}
                onChange={(event) => setDecisionStatus(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                {DECISION_STATUSES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
                <option value="under_review">Mark under review</option>
                <option value="suspended">Suspend</option>
                <option value="expired">Mark expired</option>
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Internal note (audited)</span>
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                rows={3}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <ActionButton type="submit" disabled={busy}>
                Apply decision
              </ActionButton>
              <ActionButton
                type="button"
                variant="outline"
                disabled={busy}
                onClick={() => void onFreeze(true)}
              >
                Freeze
              </ActionButton>
              <ActionButton
                type="button"
                variant="outline"
                disabled={busy || !selected.frozen}
                onClick={() => void onFreeze(false)}
              >
                Unfreeze
              </ActionButton>
            </div>
          </form>
          <div className="mt-4">
            <ApiNote>
              POST /api/v1/platform/kyc/cases/{"{id}"}/override supports set_status, freeze, and
              unfreeze. Decisions are audited as kyc.override.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "payout" && selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Payout gating</h2>
          <div className="mb-4 grid gap-3 sm:grid-cols-2">
            <InfoTile
              label="Payout eligible (derived)"
              value={payoutEligible(selected.status, selected.frozen) ? "Yes" : "No"}
            />
            <InfoTile label="KYC status" value={selected.status || "—"} />
            <InfoTile label="Frozen" value={selected.frozen ? "Yes" : "No"} />
            <InfoTile
              label="Rule"
              value="Must be verified and not frozen; agency must allow request_payouts"
            />
          </div>
          <ApiNote>
            SA4-004: payout eligibility is enforced server-side (payout_kyc_unverified /
            payout_kyc_frozen). Freeze override also disables agency request_payouts capability
            automatically. No separate payout-gate toggle API is required.
          </ApiNote>
        </article>
      ) : null}

      {tab === "refresh" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Re-verification / expiry</h2>
          <p className="mt-0 mb-4 text-body text-text-secondary">
            Agencies start/resume provider sessions via POST /api/v1/agency/kyc/session. Platform
            can set status to expired or incomplete as an override when needed.
          </p>
          {selected ? (
            <ActionButton
              disabled={busy}
              onClick={() =>
                void overrideCase({
                  caseId: selected.id,
                  action: "set_status",
                  status: "expired",
                  internal_note: note || "Marked expired for re-verification",
                })
              }
            >
              Mark selected case expired
            </ActionButton>
          ) : (
            <p className="m-0 text-body text-text-muted">Select a case to mark expired.</p>
          )}
          <div className="mt-4">
            <ApiNote>
              SA4-005 (Should): dedicated re-verification/expiry workflow endpoint is not available.
              expires_at is stored server-side but not returned on the cases list payload yet.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "settings" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">KYC provider settings</h2>
          <form className="grid max-w-xl gap-3" onSubmit={(event) => void onSettings(event)}>
            <Field
              label="Provider slug"
              name="provider_slug"
              defaultValue={settings?.provider_slug || ""}
            />
            <Field
              label="API key ref"
              name="api_key_ref"
              defaultValue={settings?.api_key_ref || ""}
            />
            <Field
              label="Webhook secret ref"
              name="webhook_secret_ref"
              defaultValue={settings?.webhook_secret_ref || ""}
            />
            <Field
              label="Hosted base URL"
              name="hosted_base_url"
              defaultValue={settings?.hosted_base_url || ""}
            />
            <ActionButton type="submit" disabled={busy}>
              Save settings
            </ActionButton>
          </form>
          <div className="mt-4">
            <ApiNote>
              Settings store secret references only — raw API keys/webhook secrets are never
              returned by the platform API.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {(tab === "evidence" || tab === "decision" || tab === "payout") && !selected ? (
        <p className="text-body text-text-muted">Select a case from the review queue.</p>
      ) : null}
    </section>
  );
}

function Field({
  label,
  name,
  defaultValue,
}: {
  label: string;
  name: string;
  defaultValue?: string;
}) {
  return (
    <label className="m-0 grid gap-1.5 font-normal">
      <span className="text-body-sm text-text-muted">{label}</span>
      <input
        name={name}
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
