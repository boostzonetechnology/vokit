import { FormEvent, useEffect, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { FormSectionSkeleton } from "@/components/ui/FormSectionSkeleton";
import { ListRowsSkeleton } from "@/components/ui/ListRowSkeleton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { AgentConfigureForm } from "@/features/agents/components/AgentConfigureForm";
import { AgentKnowledgePanel } from "@/features/agents/components/AgentKnowledgePanel";
import { AgentPublishPanel } from "@/features/agents/components/AgentPublishPanel";
import { useAgencyAgentsDirectory } from "./hooks/useAgencyAgentsDirectory";
import { ApiNote } from "@/features/platform/ux/ApiNote";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "paused" || value === "draft" || value === "testing") return "warning";
  if (value === "suspended" || value === "error" || value === "archived") return "danger";
  return "neutral";
}

type Tab = "configure" | "test" | "lifecycle";

export function AgencyAgentsScreen() {
  const {
    agents,
    customers,
    templates,
    calls,
    transfers,
    knowledgeSources,
    attachedKnowledge,
    knowledgeLoading,
    routing,
    routingLoading,
    selectedDetail,
    customerName,
    numberByAgent,
    error,
    message,
    loading,
    busy,
    loadAgentDetail,
    loadAgentKnowledge,
    fetchRouting,
    createAgent,
    configureAgent,
    publishAgent,
    pauseAgent,
    cloneAgent,
    startTestSession,
    attachKnowledge,
    detachKnowledge,
  } = useAgencyAgentsDirectory();

  const [query, setQuery] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [tab, setTab] = useState<Tab>("configure");
  const [showCreate, setShowCreate] = useState(false);
  const [createMode, setCreateMode] = useState<"scratch" | "template">("scratch");
  const [cloneCustomerId, setCloneCustomerId] = useState("");

  useEffect(() => {
    if (!selectedId) return;
    void loadAgentDetail(selectedId);
    setCloneCustomerId("");
  }, [selectedId, loadAgentDetail]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return agents.filter((row) => {
      if (customerFilter && row.customer_id !== customerFilter) return false;
      if (statusFilter && (row.status ?? "").toLowerCase() !== statusFilter) return false;
      if (!q) return true;
      const hay = [
        row.display_name,
        row.agent_type,
        row.status,
        row.id,
        row.customer_id,
        numberByAgent.get(row.id),
        customerName(row.customer_id),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [agents, customerFilter, statusFilter, query, numberByAgent, customerName]);

  const statusOptions = useMemo(() => {
    return [...new Set(agents.map((row) => (row.status ?? "").toLowerCase()).filter(Boolean))];
  }, [agents]);

  const agentCalls = useMemo(() => {
    if (!selectedId) return [];
    return calls.filter((row) => row.agent_id === selectedId).slice(0, 8);
  }, [calls, selectedId]);

  const detail = selectedDetail;
  const agencyLocked = Boolean(detail?.status_locked);

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createAgent({
        customer_id: String(form.get("customer_id") || ""),
        display_name: String(form.get("display_name") || ""),
        template_id:
          createMode === "template" ? String(form.get("template_id") || "") || undefined : undefined,
      });
      setShowCreate(false);
      event.currentTarget.reset();
    } catch {
      /* hook message */
    }
  }

  async function onTest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId) return;
    const form = new FormData(event.currentTarget);
    try {
      await startTestSession(selectedId, String(form.get("query") || ""));
      event.currentTarget.reset();
    } catch {
      /* hook message */
    }
  }

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Agents
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Create, configure, test, publish · AG3-001–005
          </p>
        </div>
        <ActionButton variant="outline" onClick={() => setShowCreate((value) => !value)}>
          {showCreate ? "Close form" : "Create agent"}
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

      {showCreate ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 flex flex-wrap gap-2">
            <ActionButton
              variant={createMode === "scratch" ? "secondary" : "outline"}
              onClick={() => setCreateMode("scratch")}
            >
              From scratch
            </ActionButton>
            <ActionButton
              variant={createMode === "template" ? "secondary" : "outline"}
              onClick={() => setCreateMode("template")}
            >
              From template
            </ActionButton>
          </div>
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => void onCreate(event)}>
            <FormSelect label="Customer" name="customer_id" required defaultValue="">
              <option value="" disabled>
                Select customer
              </option>
              {customers.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.display_name || row.id.slice(0, 8)}
                </option>
              ))}
            </FormSelect>
            <FormField label="Display name" name="display_name" required />
            {createMode === "template" ? (
              <div className="sm:col-span-2">
                <FormSelect label="Template" name="template_id" required defaultValue="">
                  <option value="" disabled>
                    Select template
                  </option>
                  {templates.map((row) => (
                    <option key={row.id} value={row.id}>
                      {row.name || row.id.slice(0, 8)}
                      {row.industry ? ` · ${row.industry}` : ""}
                    </option>
                  ))}
                </FormSelect>
              </div>
            ) : null}
            <div className="sm:col-span-2">
              <ActionButton type="submit" disabled={busy}>
                {createMode === "template" ? "Install template" : "Create draft"}
              </ActionButton>
            </div>
          </form>
          {createMode === "template" && templates.length === 0 ? (
            <div className="mt-3">
              <ApiNote>
                No templates available for this agency yet. Templates are platform-managed;
                agencies consume allowed templates only.
              </ApiNote>
            </div>
          ) : null}
        </article>
      ) : null}

      <div className="grid min-w-0 gap-4 lg:grid-cols-[1.1fr_1fr]">
        <article className="min-w-0 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 grid gap-3">
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Search</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Name, customer, number…"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Customer</span>
                <select
                  value={customerFilter}
                  onChange={(event) => setCustomerFilter(event.target.value)}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  <option value="">All customers</option>
                  {customers.map((row) => (
                    <option key={row.id} value={row.id}>
                      {row.display_name || row.id.slice(0, 8)}
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
          </div>

          {loading && agents.length === 0 ? (
            <ListRowsSkeleton rows={8} />
          ) : filtered.length === 0 ? (
            <p className="m-0 py-8 text-center text-body text-text-muted">No agents match.</p>
          ) : (
            <ul className="m-0 list-none space-y-2 p-0">
              {filtered.map((row) => {
                const selected = row.id === selectedId;
                return (
                  <li key={row.id}>
                    <button
                      type="button"
                      className={
                        selected
                          ? "flex w-full items-center justify-between gap-3 rounded-xl border border-brand bg-canvas px-3 py-3 text-left"
                          : "flex w-full items-center justify-between gap-3 rounded-xl border border-border-default bg-surface px-3 py-3 text-left hover:bg-canvas"
                      }
                      onClick={() => setSelectedId(row.id)}
                    >
                      <div className="min-w-0">
                        <p className="m-0 truncate font-semibold text-text-primary">
                          {row.display_name || row.id.slice(0, 8)}
                        </p>
                        <p className="m-0 text-body-sm text-text-muted">
                          {customerName(row.customer_id)} · {numberByAgent.get(row.id) || "No number"}
                        </p>
                      </div>
                      <StatusBadge tone={statusTone(row.status)}>
                        {row.status || "unknown"}
                      </StatusBadge>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </article>

        <article className="min-w-0 overflow-hidden rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          {!selectedId ? (
            <p className="m-0 py-10 text-center text-body text-text-muted">
              Select an agent to configure, test, or publish.
            </p>
          ) : !detail ? (
            <FormSectionSkeleton fields={5} />
          ) : (
            <div className="grid min-w-0 gap-4">
              <div className="flex min-w-0 flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="m-0 break-words text-section text-text-primary">
                    {detail.display_name || detail.id.slice(0, 8)}
                  </h2>
                  <p className="mt-1 mb-0 break-all text-body-sm text-text-muted">
                    {customerName(detail.customer_id)} · {detail.id}
                  </p>
                </div>
                <StatusBadge tone={statusTone(detail.status)}>
                  {detail.status || "unknown"}
                </StatusBadge>
              </div>

              <div className="flex flex-wrap gap-2">
                {(
                  [
                    { id: "configure", label: "Configure" },
                    { id: "test", label: "Test" },
                    { id: "lifecycle", label: "Publish" },
                  ] as Array<{ id: Tab; label: string }>
                ).map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={
                      tab === item.id
                        ? "rounded-xl bg-brand px-3 py-2 text-body font-semibold text-text-inverse"
                        : "rounded-xl border border-border-default bg-canvas px-3 py-2 text-body font-semibold text-text-secondary"
                    }
                    onClick={() => setTab(item.id)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              {tab === "configure" ? (
                <div className="grid gap-4">
                  <AgentConfigureForm
                    portal="agency"
                    detail={detail}
                    busy={busy}
                    disabled={agencyLocked}
                    transfers={transfers}
                    onSubmit={async (patch) => {
                      await configureAgent(selectedId, patch);
                    }}
                  />
                  <AgentKnowledgePanel
                    agentId={selectedId}
                    customerId={detail.customer_id}
                    busy={busy}
                    disabled={agencyLocked}
                    attached={attachedKnowledge}
                    available={knowledgeSources}
                    loading={knowledgeLoading}
                    onReload={() => void loadAgentKnowledge(selectedId)}
                    onAttach={async (sourceId) => {
                      await attachKnowledge(selectedId, sourceId);
                    }}
                    onDetach={async (sourceId) => {
                      await detachKnowledge(selectedId, sourceId);
                    }}
                  />
                  <ApiNote>
                    Number assignment lives on Numbers. Transfer destinations are created under
                    Transfers, then linked here as default transfer.
                  </ApiNote>
                </div>
              ) : null}

              {tab === "test" ? (
                <div className="grid gap-4">
                  <form className="grid gap-3" onSubmit={(event) => void onTest(event)}>
                    <FormField
                      label="Test query"
                      name="query"
                      placeholder="Hello, book an appointment…"
                      required
                    />
                    <ActionButton type="submit" disabled={busy}>
                      Start test session
                    </ActionButton>
                  </form>
                  <ApiNote>
                    Test sessions are text-only. They do not place a SIP call and report
                    production_routable=false by design.
                  </ApiNote>
                  <div>
                    <h3 className="m-0 mb-2 text-body font-semibold text-text-primary">
                      Recent calls for agent
                    </h3>
                    {agentCalls.length === 0 ? (
                      <p className="m-0 text-body text-text-muted">No calls yet.</p>
                    ) : (
                      <ul className="m-0 list-none space-y-2 p-0">
                        {agentCalls.map((row) => (
                          <li
                            key={row.id}
                            className="flex items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                          >
                            <span className="text-body text-text-secondary">
                              {row.id.slice(0, 8)} · {row.direction || "—"}
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
              ) : null}

              {tab === "lifecycle" ? (
                <AgentPublishPanel
                  detail={detail}
                  busy={busy}
                  routing={routing}
                  routingLoading={routingLoading}
                  customers={customers}
                  cloneCustomerId={cloneCustomerId}
                  onCloneCustomerChange={setCloneCustomerId}
                  onRefreshRouting={() => void fetchRouting(selectedId)}
                  onPublish={() => void publishAgent(selectedId)}
                  onPause={() => void pauseAgent(selectedId)}
                  onClone={() =>
                    void cloneAgent(
                      selectedId,
                      cloneCustomerId ? { customer_id: cloneCustomerId } : undefined,
                    )
                  }
                />
              ) : null}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
