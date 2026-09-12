import { FormEvent, useEffect, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
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
    selectedDetail,
    customerName,
    numberByAgent,
    error,
    message,
    loading,
    busy,
    loadAgentDetail,
    createAgent,
    configureAgent,
    publishAgent,
    pauseAgent,
    cloneAgent,
    startTestSession,
  } = useAgencyAgentsDirectory();

  const [query, setQuery] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [tab, setTab] = useState<Tab>("configure");
  const [showCreate, setShowCreate] = useState(false);
  const [createMode, setCreateMode] = useState<"scratch" | "template">("scratch");

  useEffect(() => {
    if (!selectedId) return;
    void loadAgentDetail(selectedId);
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

  async function onConfigure(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId) return;
    const form = new FormData(event.currentTarget);
    try {
      await configureAgent(selectedId, {
        display_name: String(form.get("display_name") || ""),
        language: String(form.get("language") || ""),
        voice_provider: String(form.get("voice_provider") || ""),
        voice_id: String(form.get("voice_id") || ""),
        timezone: String(form.get("timezone") || ""),
        greeting: String(form.get("greeting") || ""),
        instructions: String(form.get("instructions") || ""),
        fallback_behavior: String(form.get("fallback_behavior") || ""),
        inbound_enabled: form.get("inbound_enabled") === "on",
        outbound_enabled: form.get("outbound_enabled") === "on",
        recording_disclosure: form.get("recording_disclosure") === "on",
      });
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

  const detail = selectedDetail;

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Agents
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Create, configure, test, publish · AG3
          </p>
        </div>
        <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
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

      <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
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

          {loading ? (
            <p className="m-0 text-body text-text-muted" role="status">
              Loading agents…
            </p>
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

        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          {!selectedId ? (
            <p className="m-0 py-10 text-center text-body text-text-muted">
              Select an agent to configure, test, or publish.
            </p>
          ) : !detail ? (
            <p className="m-0 text-body text-text-muted" role="status">
              Loading agent detail…
            </p>
          ) : (
            <div className="grid gap-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="m-0 text-section text-text-primary">
                    {detail.display_name || detail.id.slice(0, 8)}
                  </h2>
                  <p className="mt-1 mb-0 text-body-sm text-text-muted">
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
                <form className="grid gap-3" onSubmit={(event) => void onConfigure(event)}>
                  <FormField
                    label="Display name"
                    name="display_name"
                    defaultValue={detail.display_name || ""}
                  />
                  <div className="grid gap-3 sm:grid-cols-2">
                    <FormField
                      label="Language"
                      name="language"
                      defaultValue={detail.language || ""}
                    />
                    <FormField
                      label="Timezone"
                      name="timezone"
                      defaultValue={detail.timezone || ""}
                    />
                    <FormField
                      label="Voice provider"
                      name="voice_provider"
                      defaultValue={detail.voice_provider || ""}
                    />
                    <FormField
                      label="Voice id"
                      name="voice_id"
                      defaultValue={detail.voice_id || ""}
                    />
                  </div>
                  <FormField
                    label="Greeting"
                    name="greeting"
                    defaultValue={detail.greeting || ""}
                  />
                  <label className="m-0 grid gap-1.5 font-normal">
                    <span className="text-body-sm text-text-muted">Instructions</span>
                    <textarea
                      name="instructions"
                      rows={4}
                      defaultValue={detail.instructions || ""}
                      className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                    />
                  </label>
                  <FormField
                    label="Fallback behavior"
                    name="fallback_behavior"
                    defaultValue={detail.fallback_behavior || ""}
                  />
                  <div className="flex flex-wrap gap-4">
                    <label className="m-0 flex items-center gap-2 font-normal text-body">
                      <input
                        type="checkbox"
                        name="inbound_enabled"
                        defaultChecked={Boolean(detail.inbound_enabled)}
                      />
                      Inbound enabled
                    </label>
                    <label className="m-0 flex items-center gap-2 font-normal text-body">
                      <input
                        type="checkbox"
                        name="outbound_enabled"
                        defaultChecked={Boolean(detail.outbound_enabled)}
                      />
                      Outbound enabled
                    </label>
                    <label className="m-0 flex items-center gap-2 font-normal text-body">
                      <input
                        type="checkbox"
                        name="recording_disclosure"
                        defaultChecked={Boolean(detail.recording_disclosure)}
                      />
                      Recording disclosure
                    </label>
                  </div>
                  <ActionButton type="submit" disabled={busy}>
                    Save configuration
                  </ActionButton>
                  <ApiNote>
                    Knowledge attach, transfer destination, and number assignment live on their
                    own modules (/knowledge, /transfers, /numbers). This form covers voice,
                    language, instructions, hours-related flags, and behavior fields exposed by
                    PATCH /agency/agents/{"{id}"}.
                  </ApiNote>
                </form>
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
                <div className="grid gap-3">
                  <p className="m-0 text-body text-text-secondary">
                    Publish/pause are subject to customer plan, balance, and status on the server
                    (AG3-004).
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <ActionButton disabled={busy} onClick={() => void publishAgent(selectedId)}>
                      Publish / activate
                    </ActionButton>
                    <ActionButton
                      variant="outline"
                      disabled={busy}
                      onClick={() => void pauseAgent(selectedId)}
                    >
                      Pause / deactivate
                    </ActionButton>
                    <ActionButton
                      variant="secondary"
                      disabled={busy}
                      onClick={() => void cloneAgent(selectedId)}
                    >
                      Clone
                    </ActionButton>
                  </div>
                  <ApiNote>
                    Clone stays within the same agency/customer boundary enforced by the API
                    (AG3-005 Should).
                  </ApiNote>
                </div>
              ) : null}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
