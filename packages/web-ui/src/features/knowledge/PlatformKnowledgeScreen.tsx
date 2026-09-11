import { FormEvent, useState, type ReactNode } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { usePlatformKnowledge } from "./hooks/usePlatformKnowledge";
import { KNOWLEDGE_KINDS } from "./types";

type Tab = "sources" | "tenant" | "processing";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "ready") return "success";
  if (value === "failed") return "danger";
  if (value === "processing" || value === "uploaded") return "warning";
  if (value === "stale") return "neutral";
  return "neutral";
}

function ApiNote({ children }: { children: ReactNode }) {
  return (
    <p className="m-0 rounded-lg border border-dashed border-border-strong bg-canvas px-3 py-2 text-body-sm text-text-muted">
      {children}
    </p>
  );
}

export function PlatformKnowledgeScreen() {
  const {
    sources,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    kindFilter,
    setKindFilter,
    reload,
    createSource,
  } = usePlatformKnowledge();

  const [showCreate, setShowCreate] = useState(false);
  const [tab, setTab] = useState<Tab>("sources");
  const [kind, setKind] = useState("text");

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createSource({
        title: String(form.get("title") || ""),
        body: String(form.get("body") || ""),
        kind,
      });
      setShowCreate(false);
      event.currentTarget.reset();
      setKind("text");
      setTab("sources");
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "sources", label: "Global sources" },
    { id: "tenant", label: "Agency / customer" },
    { id: "processing", label: "Processing state" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Knowledge
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA8-001–004 · Permission: agents.review
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close form" : "Add global source"}
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

      {showCreate && tab === "sources" ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 text-section text-text-primary">Create global knowledge</h2>
          <p className="mt-1 mb-4 text-body-sm text-text-muted">
            POST /api/v1/platform/knowledge — scope is always global for this route.
          </p>
          <form className="grid gap-4" onSubmit={(event) => void onCreate(event)}>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Title</span>
                <input
                  name="title"
                  required
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                />
              </label>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Kind</span>
                <select
                  value={kind}
                  onChange={(event) => setKind(event.target.value)}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  {KNOWLEDGE_KINDS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">
                {kind === "qa"
                  ? "Q&A body"
                  : kind === "file" || kind === "url"
                    ? "Extracted text (required)"
                    : "Body"}
              </span>
              <textarea
                name="body"
                required
                rows={8}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            {(kind === "file" || kind === "url") && (
              <ApiNote>
                Remote fetch is disabled. For file/URL kinds the API requires extracted text in
                the body field; upload/crawl pipelines are not exposed on this route.
              </ApiNote>
            )}
            <div>
              <ActionButton type="submit" disabled={busy}>
                Create source
              </ActionButton>
            </div>
          </form>
        </article>
      ) : null}

      {tab === "sources" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 grid gap-3 lg:grid-cols-2">
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Search</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Title, scope, id…"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Kind</span>
              <select
                value={kindFilter}
                onChange={(event) => setKindFilter(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="">All</option>
                {KNOWLEDGE_KINDS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <h2 className="m-0 mb-3 text-section text-text-primary">
            Global catalog
            <span className="ml-2 text-body font-normal text-text-muted">({sources.length})</span>
          </h2>

          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading knowledge…</p>
          ) : sources.length === 0 ? (
            <p className="m-0 py-10 text-center text-body text-text-muted">
              No global knowledge sources yet.
            </p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Title</th>
                    <th className="border-0 px-2 py-2 text-left">Scope</th>
                    <th className="border-0 px-2 py-2 text-left">Kind</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map((row) => (
                    <tr
                      key={row.id}
                      className={
                        selectedId === row.id
                          ? "cursor-pointer bg-brand-subtle/40"
                          : "cursor-pointer hover:bg-canvas"
                      }
                      onClick={() => setSelectedId(row.id)}
                    >
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.title || row.id.slice(0, 8)}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.scope || "global"}</td>
                      <td className="px-2 py-3 text-text-secondary">{row.kind || "—"}</td>
                      <td className="px-2 py-3">
                        {row.status ? (
                          <StatusBadge tone={statusTone(row.status)}>{row.status}</StatusBadge>
                        ) : (
                          <span className="text-text-muted">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {selected ? (
            <div className="mt-4 grid gap-2 rounded-xl border border-border-default bg-canvas p-4">
              <p className="m-0 font-semibold text-text-primary">
                {selected.title || selected.id}
              </p>
              <p className="m-0 text-body-sm text-text-muted">{selected.id}</p>
              <ApiNote>
                Platform list returns id, title, and scope. Kind/status may be missing on list
                responses even though create returns status=ready.
              </ApiNote>
            </div>
          ) : null}
        </article>
      ) : null}

      {tab === "tenant" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">
            Agency / customer knowledge
          </h2>
          <p className="mt-0 mb-4 text-body text-text-secondary">
            Tenant knowledge is managed under agency/customer APIs with authorization. Super
            Admin inspection of tenant sources requires a privileged platform route.
          </p>
          <ActionButton disabled title="API not available yet">
            Inspect tenant knowledge
          </ActionButton>
          <div className="mt-4 grid gap-2">
            <ApiNote>
              SA8-002: there is no platform endpoint to list or inspect agency/customer
              knowledge with Super Admin authorization. Use agency portal knowledge routes for
              tenant-owned sources.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "processing" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-section text-text-primary">Processing states</h2>
          <p className="mt-0 mb-4 text-body text-text-secondary">
            Domain statuses: uploaded, processing, ready, failed, stale. Successful global
            ingest currently returns ready immediately.
          </p>
          <div className="mb-4 flex flex-wrap gap-2">
            {(["uploaded", "processing", "ready", "failed", "stale"] as const).map((status) => (
              <StatusBadge key={status} tone={statusTone(status)}>
                {status}
              </StatusBadge>
            ))}
          </div>
          <ApiNote>
            SA8-004: platform GET /api/v1/platform/knowledge list does not reliably include
            processing status columns. Async uploaded→processing→ready/failed/stale lifecycle
            UI needs list/detail fields from the API before it can be driven live.
          </ApiNote>
        </article>
      ) : null}
    </section>
  );
}
