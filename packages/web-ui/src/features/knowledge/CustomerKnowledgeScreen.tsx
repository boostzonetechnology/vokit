import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useCustomerKnowledge } from "./hooks/useCustomerKnowledge";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "ready") return "success";
  if (value === "processing" || value === "uploaded") return "warning";
  if (value === "failed" || value === "stale") return "danger";
  return "neutral";
}

export function CustomerKnowledgeScreen() {
  const {
    sources,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    query,
    setQuery,
    reload,
  } = useCustomerKnowledge();

  return (
    <section className="mx-auto max-w-[1100px]">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Knowledge
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Customer sources attached to agents · CU6
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

      <div className="mb-4">
        <FormField
          label="Search"
          name="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Sources ({sources.length})
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading…</p>
          ) : !sources.length ? (
            <p className="m-0 text-body text-text-muted">No customer knowledge sources.</p>
          ) : (
            <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
              {sources.map((row) => (
                <li key={row.id}>
                  <button
                    type="button"
                    className={`w-full rounded-lg border px-3 py-2 text-left ${
                      selectedId === row.id
                        ? "border-border-brand bg-surface-muted"
                        : "border-border-default"
                    }`}
                    onClick={() => setSelectedId(row.id)}
                  >
                    <div className="flex justify-between gap-2">
                      <span className="font-medium text-text-primary">
                        {row.title || row.id.slice(0, 8)}
                      </span>
                      <StatusBadge tone={statusTone(row.status)}>
                        {row.status || "—"}
                      </StatusBadge>
                    </div>
                    <p className="m-0 mt-1 text-sm text-text-muted">{row.scope || "customer"}</p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">Detail</h2>
          {!selected ? (
            <p className="m-0 text-body text-text-muted">Select a source.</p>
          ) : (
            <dl className="m-0 grid gap-2 text-sm">
              <div>
                <dt className="text-text-muted">Title</dt>
                <dd className="m-0 text-text-primary">{selected.title}</dd>
              </div>
              <div>
                <dt className="text-text-muted">Scope / status</dt>
                <dd className="m-0 text-text-primary">
                  {selected.scope || "—"} · {selected.status || "—"}
                </dd>
              </div>
            </dl>
          )}
          <ApiNote>
            CU6-001 — view customer knowledge. CU6-002 edit/upload requires agency grant and is not
            on the customer write API yet.
          </ApiNote>
        </article>
      </div>
    </section>
  );
}
