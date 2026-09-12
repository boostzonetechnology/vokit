import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { KNOWLEDGE_KINDS } from "@/features/knowledge/types";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyKnowledge } from "./hooks/useAgencyKnowledge";

type Tab = "sources" | "attach" | "sync";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "ready") return "success";
  if (value === "processing" || value === "uploaded") return "warning";
  if (value === "failed" || value === "stale") return "danger";
  return "neutral";
}

export function AgencyKnowledgeScreen() {
  const {
    sources,
    customers,
    agents,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    scopeFilter,
    setScopeFilter,
    reload,
    createSource,
    attachToAgent,
  } = useAgencyKnowledge();

  const [tab, setTab] = useState<Tab>("sources");
  const [showCreate, setShowCreate] = useState(false);
  const [createScope, setCreateScope] = useState<"agency" | "customer">("agency");
  const [attachAgentId, setAttachAgentId] = useState("");

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createSource({
        title: String(form.get("title") || ""),
        body: String(form.get("body") || ""),
        kind: String(form.get("kind") || "text"),
        scope: createScope,
        owner_id:
          createScope === "customer" ? String(form.get("owner_id") || "") : undefined,
      });
      setShowCreate(false);
      event.currentTarget.reset();
    } catch {
      /* hook message */
    }
  }

  async function onAttach() {
    if (!selectedId || !attachAgentId) return;
    try {
      await attachToAgent(attachAgentId, selectedId);
    } catch {
      /* hook message */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "sources", label: "Sources" },
    { id: "attach", label: "Agent attach" },
    { id: "sync", label: "Sync / reindex" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Knowledge
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Agency & customer sources, agent attach · AG7
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close form" : "Add source"}
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

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((item) => (
          <ActionButton
            key={item.id}
            variant={tab === item.id ? "secondary" : "outline"}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </ActionButton>
        ))}
      </div>

      {showCreate ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-3 flex flex-wrap gap-2">
            <ActionButton
              variant={createScope === "agency" ? "secondary" : "outline"}
              onClick={() => setCreateScope("agency")}
            >
              Agency-wide
            </ActionButton>
            <ActionButton
              variant={createScope === "customer" ? "secondary" : "outline"}
              onClick={() => setCreateScope("customer")}
            >
              Customer-specific
            </ActionButton>
          </div>
          <form className="grid gap-3" onSubmit={(event) => void onCreate(event)}>
            <div className="grid gap-3 sm:grid-cols-2">
              <FormField label="Title" name="title" required />
              <FormSelect label="Kind" name="kind" required defaultValue="text">
                {KNOWLEDGE_KINDS.map((kind) => (
                  <option key={kind.value} value={kind.value}>
                    {kind.label}
                  </option>
                ))}
              </FormSelect>
              {createScope === "customer" ? (
                <FormSelect label="Customer" name="owner_id" required defaultValue="">
                  <option value="" disabled>
                    Select customer
                  </option>
                  {customers.map((row) => (
                    <option key={row.id} value={row.id}>
                      {row.display_name || row.id.slice(0, 8)}
                    </option>
                  ))}
                </FormSelect>
              ) : null}
            </div>
            <label className="grid gap-1 text-sm text-text-muted">
              Content / extracted text
              <textarea
                name="body"
                required
                rows={5}
                className="rounded-xl border border-border-default bg-surface px-4 py-3 text-text-primary outline-none focus:border-brand"
              />
            </label>
            <ActionButton type="submit" disabled={busy}>
              Create source
            </ActionButton>
          </form>
          <ApiNote>
            AG7-001 / AG7-002 — agency-wide vs customer-scoped sources. File/URL kinds currently
            ingest provided text payload.
          </ApiNote>
        </article>
      ) : null}

      {tab === "sync" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Sync / reindex
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Refresh for URL/file sources is not yet exposed on the agency knowledge API. Re-create
            or re-ingest content when source material changes.
          </p>
          <ApiNote>AG7-004 (Should) — pending reindex endpoint.</ApiNote>
        </article>
      ) : (
        <>
          <div className="mb-4 grid gap-3 sm:grid-cols-2">
            <FormField
              label="Search"
              name="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Title, scope, status…"
            />
            <FormSelect
              label="Scope"
              name="scope"
              value={scopeFilter}
              onChange={(event) => setScopeFilter(event.target.value)}
            >
              <option value="">All scopes</option>
              <option value="agency">Agency</option>
              <option value="customer">Customer</option>
            </FormSelect>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                Sources ({sources.length})
              </h2>
              {loading ? (
                <p className="m-0 text-body text-text-muted" role="status">
                  Loading…
                </p>
              ) : !sources.length ? (
                <p className="m-0 text-body text-text-muted">No knowledge sources yet.</p>
              ) : (
                <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
                  {sources.map((row) => (
                    <li key={row.id}>
                      <button
                        type="button"
                        className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                          selectedId === row.id
                            ? "border-border-brand bg-surface-muted"
                            : "border-border-default bg-surface hover:bg-surface-muted"
                        }`}
                        onClick={() => setSelectedId(row.id)}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium text-text-primary">
                            {row.title || row.id.slice(0, 8)}
                          </span>
                          <StatusBadge tone={statusTone(row.status)}>
                            {row.status || "—"}
                          </StatusBadge>
                        </div>
                        <p className="m-0 mt-1 text-sm text-text-muted">
                          {row.scope || "—"}
                          {row.kind ? ` · ${row.kind}` : ""}
                        </p>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </article>

            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              {tab === "attach" ? (
                <div className="grid gap-3">
                  <h2 className="m-0 text-[1.05rem] font-semibold text-text-primary">
                    Attach to agent
                  </h2>
                  {!selected ? (
                    <p className="m-0 text-body text-text-muted">Select a source first.</p>
                  ) : (
                    <>
                      <p className="m-0 text-body text-text-muted">
                        Attaching “{selected.title || selected.id.slice(0, 8)}”
                      </p>
                      <FormSelect
                        label="Agent"
                        name="agent_id"
                        value={attachAgentId}
                        onChange={(event) => setAttachAgentId(event.target.value)}
                      >
                        <option value="">Select agent</option>
                        {agents.map((row) => (
                          <option key={row.id} value={row.id}>
                            {row.display_name || row.id.slice(0, 8)}
                          </option>
                        ))}
                      </FormSelect>
                      <ActionButton
                        disabled={busy || !attachAgentId}
                        onClick={() => void onAttach()}
                      >
                        Attach source
                      </ActionButton>
                      <ApiNote>
                        AG7-003 — attach/detach allowed sources. Detach API is not yet exposed;
                        attach updates the agent allowlist.
                      </ApiNote>
                    </>
                  )}
                </div>
              ) : (
                <div className="grid gap-3">
                  <h2 className="m-0 text-[1.05rem] font-semibold text-text-primary">
                    Source detail
                  </h2>
                  {!selected ? (
                    <p className="m-0 text-body text-text-muted">Select a source.</p>
                  ) : (
                    <dl className="m-0 grid gap-2 text-sm">
                      <div>
                        <dt className="text-text-muted">Title</dt>
                        <dd className="m-0 text-text-primary">{selected.title}</dd>
                      </div>
                      <div>
                        <dt className="text-text-muted">Scope</dt>
                        <dd className="m-0 text-text-primary">{selected.scope || "—"}</dd>
                      </div>
                      <div>
                        <dt className="text-text-muted">Status</dt>
                        <dd className="m-0">
                          <StatusBadge tone={statusTone(selected.status)}>
                            {selected.status || "—"}
                          </StatusBadge>
                        </dd>
                      </div>
                    </dl>
                  )}
                </div>
              )}
            </article>
          </div>
        </>
      )}
    </section>
  );
}
