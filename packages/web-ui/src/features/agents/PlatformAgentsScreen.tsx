import { FormEvent, useEffect, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormSectionSkeleton } from "@/components/ui/FormSectionSkeleton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { TableSkeleton } from "@/components/ui/TableSkeleton";
import { AgentConfigureForm } from "@/features/agents/components/AgentConfigureForm";
import { usePlatformAgentsDirectory } from "./hooks/usePlatformAgentsDirectory";
import type { PlatformAgentDetail, PlatformAgentDiagnostics } from "./types";
import type { TransferDestination } from "@/features/transfers/types";
import { ApiNote } from "@/features/platform/ux/ApiNote";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "paused" || value === "draft" || value === "testing") return "warning";
  if (value === "suspended" || value === "error" || value === "archived") return "danger";
  return "neutral";
}

type Tab = "manage" | "diagnostics" | "override";

export function PlatformAgentsScreen() {
  const {
    agents,
    customers,
    transfers,
    selectedDetail,
    diagnostics,
    agencyName,
    customerName,
    numberByAgent,
    error,
    message,
    loading,
    busy,
    detailLoading,
    diagnosticsLoading,
    loadAgentDetail,
    loadDiagnostics,
    clearSelectionSideState,
    createAgent,
    configureAgent,
    publishAgent,
    pauseAgent,
    archiveAgent,
    disableAgent,
    restoreAgent,
    cloneAgent,
  } = usePlatformAgentsDirectory();

  const [query, setQuery] = useState("");
  const [agencyFilter, setAgencyFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [tab, setTab] = useState<Tab>("manage");
  const [showCreate, setShowCreate] = useState(false);
  const [actionReason, setActionReason] = useState("");
  const [cloneCustomerId, setCloneCustomerId] = useState("");
  const [cloneName, setCloneName] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return agents.filter((row) => {
      if (agencyFilter && row.agency_id !== agencyFilter) return false;
      if (statusFilter && (row.status ?? "").toLowerCase() !== statusFilter) return false;
      if (!q) return true;
      const hay = [
        row.display_name,
        row.agent_type,
        row.status,
        row.id,
        row.agency_id,
        row.customer_id,
        row.assigned_e164,
        numberByAgent.get(row.id),
        agencyName(row.agency_id),
        customerName(row.customer_id),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [agents, agencyFilter, statusFilter, query, numberByAgent, agencyName, customerName]);

  const selected = agents.find((row) => row.id === selectedId) ?? null;
  const detail = selectedDetail?.id === selectedId ? selectedDetail : null;

  const agencyOptions = useMemo(() => {
    const ids = [...new Set(agents.map((row) => row.agency_id).filter(Boolean))] as string[];
    return ids.map((id) => ({ id, label: agencyName(id) }));
  }, [agents, agencyName]);

  const statusOptions = useMemo(() => {
    return [...new Set(agents.map((row) => (row.status ?? "").toLowerCase()).filter(Boolean))];
  }, [agents]);

  useEffect(() => {
    if (!selectedId) {
      clearSelectionSideState();
      return;
    }
    void loadAgentDetail(selectedId);
  }, [selectedId, loadAgentDetail, clearSelectionSideState]);

  useEffect(() => {
    if (!selectedId || tab !== "diagnostics") return;
    void loadDiagnostics(selectedId);
  }, [selectedId, tab, loadDiagnostics]);

  useEffect(() => {
    if (!detail) return;
    setCloneCustomerId(detail.customer_id || "");
    setCloneName(`${detail.display_name || "Agent"} (clone)`);
    setActionReason("");
  }, [detail?.id, detail?.customer_id, detail?.display_name]);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createAgent({
        customer_id: String(form.get("customer_id") || ""),
        display_name: String(form.get("display_name") || ""),
      });
      setShowCreate(false);
      event.currentTarget.reset();
    } catch {
      /* message set in hook */
    }
  }

  function requireReason(): string | null {
    const reason = actionReason.trim();
    if (!reason) return null;
    return reason;
  }

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Agents
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Global directory across tenants · SA5-001–004 · Permissions: agent.view /
            agent.update
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close form" : "Create agent"}
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
          <h2 className="m-0 text-section text-text-primary">Create agent draft</h2>
          <p className="mt-1 mb-4 text-body-sm text-text-muted">
            Privileged create onto any customer · POST /platform/agents
          </p>
          <form
            className="grid gap-3 sm:grid-cols-[1.2fr_1fr_auto] sm:items-end"
            onSubmit={(event) => void onCreate(event)}
          >
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Customer</span>
              <select
                name="customer_id"
                required
                defaultValue=""
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="" disabled>
                  Select customer
                </option>
                {customers.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.display_name || row.id.slice(0, 8)} ({agencyName(row.agency_id)})
                  </option>
                ))}
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Display name</span>
              <input
                name="display_name"
                required
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <ActionButton type="submit" disabled={busy}>
              Create draft
            </ActionButton>
          </form>
        </article>
      ) : null}

      <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <div className="mb-4 grid gap-3 lg:grid-cols-[1.4fr_1fr_1fr]">
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Search</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Name, type, agency, number…"
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Agency</span>
            <select
              value={agencyFilter}
              onChange={(event) => setAgencyFilter(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">All agencies</option>
              {agencyOptions.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.label}
                </option>
              ))}
            </select>
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Status</span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">All statuses</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>
        </div>

        <h2 className="m-0 mb-3 text-section text-text-primary">
          Global agent directory
          <span className="ml-2 text-body font-normal text-text-muted">
            ({filtered.length})
          </span>
        </h2>

        {loading && agents.length === 0 ? (
          <TableSkeleton
            headers={["Agent", "Agency", "Customer", "Status", "Type", "Number"]}
            rows={8}
          />
        ) : filtered.length === 0 ? (
          <p className="m-0 py-10 text-center text-body text-text-muted">No agents found.</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Agent</th>
                  <th className="border-0 px-2 py-2 text-left">Agency</th>
                  <th className="border-0 px-2 py-2 text-left">Customer</th>
                  <th className="border-0 px-2 py-2 text-left">Status</th>
                  <th className="border-0 px-2 py-2 text-left">Type</th>
                  <th className="border-0 px-2 py-2 text-left">Number</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr
                    key={row.id}
                    className={
                      selectedId === row.id
                        ? "bg-brand-subtle/40 cursor-pointer"
                        : "cursor-pointer hover:bg-canvas"
                    }
                    onClick={() => {
                      setSelectedId(row.id);
                      setTab("manage");
                    }}
                  >
                    <td className="px-2 py-3">
                      <p className="m-0 font-semibold text-text-primary">
                        {row.display_name || row.id.slice(0, 8)}
                      </p>
                      <p className="m-0 text-body-sm text-text-muted">{row.id.slice(0, 8)}</p>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{agencyName(row.agency_id)}</td>
                    <td className="px-2 py-3 text-text-secondary">
                      {customerName(row.customer_id)}
                    </td>
                    <td className="px-2 py-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                        {row.status_locked ? (
                          <StatusBadge tone="warning">locked</StatusBadge>
                        ) : null}
                      </div>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{row.agent_type || "—"}</td>
                    <td className="px-2 py-3 text-text-secondary">
                      {numberByAgent.get(row.id) || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      {selected ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="m-0 text-section text-text-primary">
                {(detail || selected).display_name || selected.id.slice(0, 8)}
              </h2>
              <p className="mt-1 mb-0 text-body text-text-muted">
                {agencyName(selected.agency_id)} · {customerName(selected.customer_id)} ·{" "}
                {numberByAgent.get(selected.id) || "—"}
              </p>
            </div>
            <ActionButton
              variant="secondary"
              onClick={() => {
                setSelectedId("");
                clearSelectionSideState();
              }}
            >
              Close
            </ActionButton>
          </div>

          <div className="mb-4 flex flex-wrap gap-2">
            {(
              [
                { id: "manage", label: "Manage" },
                { id: "diagnostics", label: "Diagnostics" },
                { id: "override", label: "Override" },
              ] as Array<{ id: Tab; label: string }>
            ).map((item) => (
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

          {detailLoading && !detail ? (
            <FormSectionSkeleton fields={6} />
          ) : !detail ? (
            <p className="m-0 text-body text-text-muted">Agent detail unavailable.</p>
          ) : tab === "manage" ? (
            <ManageTab
              detail={detail}
              busy={busy}
              transfers={transfers}
              actionReason={actionReason}
              cloneCustomerId={cloneCustomerId}
              cloneName={cloneName}
              customers={customers}
              agencyName={agencyName}
              onActionReasonChange={setActionReason}
              onCloneCustomerChange={setCloneCustomerId}
              onCloneNameChange={setCloneName}
              onConfigure={async (patch) => {
                await configureAgent(selectedId, patch);
              }}
              onPublish={() => void publishAgent(selectedId)}
              onPause={() => {
                const reason = requireReason();
                if (!reason) return;
                void pauseAgent(selectedId, reason);
              }}
              onArchive={() => {
                const reason = requireReason();
                if (!reason) return;
                void archiveAgent(selectedId, reason);
              }}
              onClone={() => {
                if (!cloneCustomerId) return;
                void cloneAgent(selectedId, {
                  customer_id: cloneCustomerId,
                  display_name: cloneName,
                });
              }}
              onRestore={() => void restoreAgent(selectedId, "active")}
            />
          ) : tab === "diagnostics" ? (
            <DiagnosticsTab
              loading={diagnosticsLoading}
              diagnostics={diagnostics}
            />
          ) : (
            <OverrideTab
              detail={detail}
              busy={busy}
              actionReason={actionReason}
              onActionReasonChange={setActionReason}
              onDisable={() => {
                const reason = requireReason();
                if (!reason) return;
                void disableAgent(selectedId, reason);
              }}
              onRestore={() => void restoreAgent(selectedId, "active")}
            />
          )}
        </article>
      ) : (
        <p className="text-body text-text-muted">
          Select an agent to manage, diagnose, or override.
        </p>
      )}
    </section>
  );
}

function ManageTab({
  detail,
  busy,
  transfers,
  actionReason,
  cloneCustomerId,
  cloneName,
  customers,
  agencyName,
  onActionReasonChange,
  onCloneCustomerChange,
  onCloneNameChange,
  onConfigure,
  onPublish,
  onPause,
  onArchive,
  onClone,
  onRestore,
}: {
  detail: PlatformAgentDetail;
  busy: boolean;
  transfers: TransferDestination[];
  actionReason: string;
  cloneCustomerId: string;
  cloneName: string;
  customers: Array<{ id: string; display_name?: string; agency_id?: string }>;
  agencyName: (id?: string) => string;
  onActionReasonChange: (value: string) => void;
  onCloneCustomerChange: (value: string) => void;
  onCloneNameChange: (value: string) => void;
  onConfigure: (patch: Record<string, unknown>) => Promise<void>;
  onPublish: () => void;
  onPause: () => void;
  onArchive: () => void;
  onClone: () => void;
  onRestore: () => void;
}) {
  const locked = Boolean(detail.status_locked);
  const archived = (detail.status ?? "").toLowerCase() === "archived";

  return (
    <div className="grid gap-6">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <InfoTile label="Status" value={detail.status || "—"} />
        <InfoTile label="Type" value={detail.agent_type || "—"} />
        <InfoTile
          label="Published version"
          value={detail.published_version == null ? "—" : String(detail.published_version)}
        />
        <InfoTile
          label="Production routable"
          value={detail.production_routable ? "Yes" : "No"}
        />
        <InfoTile label="Status lock" value={locked ? `Yes (${detail.status_actor || "—"})` : "No"} />
        <InfoTile label="Assigned number" value={detail.assigned_e164 || "—"} />
      </div>

      <div className="grid min-w-0 gap-3">
        <h3 className="m-0 text-section text-text-primary">Configure</h3>
        <AgentConfigureForm
          portal="platform"
          detail={detail}
          busy={busy}
          disabled={archived}
          transfers={transfers}
          onSubmit={onConfigure}
        />
        <ApiNote>
          Platform configure uses the same builder fields as Agency (including business hours).
          Knowledge attach stays on the Knowledge module for agencies. Archived agents must be
          restored before editing.
        </ApiNote>
      </div>

      <div className="grid gap-3">
        <h3 className="m-0 text-section text-text-primary">Lifecycle</h3>
        <label className="m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">
            Reason (required for pause / archive)
          </span>
          <input
            value={actionReason}
            onChange={(event) => onActionReasonChange(event.target.value)}
            placeholder="e.g. Abuse review, billing hold…"
            className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
          />
        </label>
        <div className="flex flex-wrap gap-2">
          <ActionButton disabled={busy || archived} onClick={onPublish}>
            Publish
          </ActionButton>
          <ActionButton
            variant="outline"
            disabled={busy || !actionReason.trim()}
            onClick={onPause}
          >
            Pause
          </ActionButton>
          <ActionButton
            variant="outline"
            disabled={busy || !actionReason.trim()}
            onClick={onArchive}
          >
            Archive
          </ActionButton>
          {locked || archived ? (
            <ActionButton variant="secondary" disabled={busy} onClick={onRestore}>
              Restore to active
            </ActionButton>
          ) : null}
        </div>
      </div>

      <div className="grid gap-3">
        <h3 className="m-0 text-section text-text-primary">Clone</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Target customer</span>
            <select
              value={cloneCustomerId}
              onChange={(event) => onCloneCustomerChange(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            >
              <option value="">Select customer</option>
              {customers.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.display_name || row.id.slice(0, 8)} ({agencyName(row.agency_id)})
                </option>
              ))}
            </select>
          </label>
          <label className="m-0 grid gap-1.5 font-normal">
            <span className="text-body-sm text-text-muted">Clone display name</span>
            <input
              value={cloneName}
              onChange={(event) => onCloneNameChange(event.target.value)}
              className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
            />
          </label>
        </div>
        <ActionButton
          variant="secondary"
          disabled={busy || !cloneCustomerId}
          onClick={onClone}
        >
          Clone to customer
        </ActionButton>
      </div>
    </div>
  );
}

function DiagnosticsTab({
  loading,
  diagnostics,
}: {
  loading: boolean;
  diagnostics: PlatformAgentDiagnostics | null;
}) {
  if (loading && !diagnostics) {
    return <FormSectionSkeleton fields={4} />;
  }
  if (!diagnostics) {
    return <p className="m-0 text-body text-text-muted">Diagnostics unavailable.</p>;
  }

  const runtime = diagnostics.runtime ?? {};
  const calls = diagnostics.recent_calls ?? [];
  const errors = diagnostics.errors ?? [];
  const integrations = diagnostics.integrations ?? [];

  return (
    <div className="grid gap-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <InfoTile
          label="Routable"
          value={runtime.production_routable ? "Yes" : "No"}
        />
        <InfoTile label="Runtime reason" value={runtime.reason || "—"} />
        <InfoTile
          label="Resolved instructions"
          value={
            runtime.resolved_instructions
              ? `${runtime.resolved_instructions.slice(0, 80)}${
                  runtime.resolved_instructions.length > 80 ? "…" : ""
                }`
              : "—"
          }
        />
      </div>

      <div>
        <h3 className="m-0 mb-2 text-section text-text-primary">Errors</h3>
        {errors.length === 0 ? (
          <p className="m-0 text-body text-text-muted">No recent errors.</p>
        ) : (
          <ul className="m-0 list-none space-y-2 p-0">
            {errors.map((row) => (
              <li
                key={row.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border-default px-3 py-2.5"
              >
                <span className="text-body text-text-primary">
                  {row.kind || "error"} · {row.id.slice(0, 8)}
                </span>
                <StatusBadge tone={statusTone(row.status)}>{row.status || "—"}</StatusBadge>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <h3 className="m-0 mb-2 text-section text-text-primary">Recent calls</h3>
        {calls.length === 0 ? (
          <p className="m-0 text-body text-text-muted">No recent calls.</p>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-label uppercase text-text-muted">
                  <th className="border-0 px-2 py-2 text-left">Call</th>
                  <th className="border-0 px-2 py-2 text-left">Direction</th>
                  <th className="border-0 px-2 py-2 text-left">Status</th>
                  <th className="border-0 px-2 py-2 text-left">Minutes</th>
                </tr>
              </thead>
              <tbody>
                {calls.map((call) => (
                  <tr key={call.id}>
                    <td className="px-2 py-3 text-text-primary">
                      {call.remote_e164 || call.e164 || call.id.slice(0, 8)}
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{call.direction || "—"}</td>
                    <td className="px-2 py-3">
                      <StatusBadge tone={statusTone(call.status)}>
                        {call.status || "unknown"}
                      </StatusBadge>
                    </td>
                    <td className="px-2 py-3 text-text-secondary">
                      {call.billed_minutes ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div>
        <h3 className="m-0 mb-2 text-section text-text-primary">Integrations</h3>
        {integrations.length === 0 ? (
          <p className="m-0 text-body text-text-muted">No integrations on diagnostics.</p>
        ) : (
          <ul className="m-0 list-none space-y-2 p-0">
            {integrations.map((row) => (
              <li
                key={row.id}
                className="flex items-center justify-between gap-3 rounded-xl border border-border-default px-3 py-2.5"
              >
                <span className="font-semibold text-text-primary">
                  {row.provider || row.id.slice(0, 8)}
                </span>
                <StatusBadge tone={statusTone(row.status)}>
                  {row.status || "unknown"}
                </StatusBadge>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function OverrideTab({
  detail,
  busy,
  actionReason,
  onActionReasonChange,
  onDisable,
  onRestore,
}: {
  detail: PlatformAgentDetail;
  busy: boolean;
  actionReason: string;
  onActionReasonChange: (value: string) => void;
  onDisable: () => void;
  onRestore: () => void;
}) {
  return (
    <div className="grid gap-4">
      <p className="m-0 text-body text-text-secondary">
        SA5-004: Super Admin can disable an agent immediately. This sets status to{" "}
        <code>suspended</code> and locks agency from changing status until you restore.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <InfoTile label="Current status" value={detail.status || "—"} />
        <InfoTile
          label="Lock"
          value={
            detail.status_locked
              ? `Locked (${detail.status_actor || "—"})`
              : "Not locked"
          }
        />
      </div>
      <label className="m-0 grid gap-1.5 font-normal">
        <span className="text-body-sm text-text-muted">Reason (required)</span>
        <input
          value={actionReason}
          onChange={(event) => onActionReasonChange(event.target.value)}
          placeholder="Abuse, billing, operational incident…"
          className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
        />
      </label>
      <div className="flex flex-wrap gap-2">
        <ActionButton
          variant="outline"
          disabled={busy || !actionReason.trim()}
          onClick={onDisable}
        >
          Disable agent now
        </ActionButton>
        <ActionButton variant="secondary" disabled={busy} onClick={onRestore}>
          Restore to active
        </ActionButton>
      </div>
    </div>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border-default bg-canvas px-3 py-3">
      <p className="m-0 text-body-sm text-text-muted">{label}</p>
      <p className="mt-1 mb-0 break-words font-semibold text-text-primary">{value}</p>
    </div>
  );
}
