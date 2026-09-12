import { FormEvent, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useCustomerAgents } from "./hooks/useCustomerAgents";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "paused" || value === "draft") return "warning";
  if (value === "suspended" || value === "error") return "danger";
  return "neutral";
}

export function CustomerAgentsScreen() {
  const {
    agents,
    detail,
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
    reload,
    saveLimitedFields,
  } = useCustomerAgents();

  const [showEdit, setShowEdit] = useState(false);
  const canEdit = Boolean(detail?.customer_can_edit);

  const statusOptions = useMemo(
    () => [...new Set(agents.map((row) => (row.status ?? "").toLowerCase()).filter(Boolean))],
    [agents],
  );

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await saveLimitedFields({
        greeting: String(form.get("greeting") || ""),
        instructions: String(form.get("instructions") || ""),
      });
      setShowEdit(false);
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
            Monitor assigned agents · CU2
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

      <div className="mb-4 grid gap-3 sm:grid-cols-2">
        <FormField
          label="Search"
          name="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <FormSelect
          label="Status"
          name="status"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="">All</option>
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </FormSelect>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Assigned agents ({agents.length})
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading…</p>
          ) : !agents.length ? (
            <p className="m-0 text-body text-text-muted">No agents assigned yet.</p>
          ) : (
            <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
              {agents.map((row) => (
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
                        {row.display_name || row.id.slice(0, 8)}
                      </span>
                      <StatusBadge tone={statusTone(row.status)}>
                        {row.status || "—"}
                      </StatusBadge>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">Detail</h2>
          {!detail ? (
            <p className="m-0 text-body text-text-muted">Select an agent.</p>
          ) : (
            <div className="grid gap-3 text-sm">
              <dl className="m-0 grid gap-2">
                <div>
                  <dt className="text-text-muted">Name</dt>
                  <dd className="m-0 text-text-primary">{detail.display_name}</dd>
                </div>
                <div>
                  <dt className="text-text-muted">Status / language</dt>
                  <dd className="m-0 text-text-primary">
                    {detail.status || "—"} · {detail.language || "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-text-muted">Voice</dt>
                  <dd className="m-0 text-text-primary">
                    {detail.voice_provider || "—"} / {detail.voice_id || "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-text-muted">Inbound / outbound</dt>
                  <dd className="m-0 text-text-primary">
                    {detail.inbound_enabled ? "Inbound on" : "Inbound off"} ·{" "}
                    {detail.outbound_enabled ? "Outbound on" : "Outbound off"}
                  </dd>
                </div>
                <div>
                  <dt className="text-text-muted">Edit permission</dt>
                  <dd className="m-0">
                    <StatusBadge tone={canEdit ? "success" : "neutral"}>
                      {canEdit ? "Granted" : "Disabled by default"}
                    </StatusBadge>
                  </dd>
                </div>
              </dl>

              <ApiNote>
                CU2-002 — editing is off unless agency/platform sets customer_can_edit.
              </ApiNote>

              {canEdit ? (
                <>
                  <ActionButton variant="outline" onClick={() => setShowEdit((v) => !v)}>
                    {showEdit ? "Close editor" : "Edit allowed fields"}
                  </ActionButton>
                  {showEdit ? (
                    <form className="grid gap-3" onSubmit={(event) => void onSave(event)}>
                      <FormField
                        label="Greeting"
                        name="greeting"
                        defaultValue={detail.greeting || ""}
                      />
                      <label className="grid gap-1 text-sm text-text-muted">
                        Instructions
                        <textarea
                          name="instructions"
                          rows={4}
                          defaultValue={detail.instructions || ""}
                          className="rounded-xl border border-border-default bg-surface px-4 py-3 text-text-primary outline-none focus:border-brand"
                        />
                      </label>
                      <ActionButton type="submit" disabled={busy}>
                        Save
                      </ActionButton>
                    </form>
                  ) : null}
                  <ApiNote>
                    CU2-003 — only greeting/instructions are editable when permission exists.
                    Pause/resume is not on the customer API yet.
                  </ApiNote>
                </>
              ) : (
                <ApiNote>
                  CU2-003 — pause/resume and field edits stay hidden until permission is granted.
                </ApiNote>
              )}
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
