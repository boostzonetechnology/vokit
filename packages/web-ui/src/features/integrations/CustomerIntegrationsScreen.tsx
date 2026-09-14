import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useCustomerIntegrations } from "./hooks/useCustomerIntegrations";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "connected" || value === "active") return "success";
  if (value === "pending") return "warning";
  if (value === "disabled" || value === "revoked") return "danger";
  return "neutral";
}

export function CustomerIntegrationsScreen() {
  const {
    providers,
    connections,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    selfServiceBlocked,
    reload,
    connect,
    testConnection,
  } = useCustomerIntegrations();

  const [showConnect, setShowConnect] = useState(false);

  async function onConnect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await connect({
        provider: String(form.get("provider") || ""),
        display_name: String(form.get("display_name") || ""),
        credential: String(form.get("credential") || ""),
      });
      setShowConnect(false);
      event.currentTarget.reset();
    } catch {
      /* hook message */
    }
  }

  return (
    <section className="mx-auto max-w-[1100px]">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Integrations
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Status & self-service connect · CU7
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowConnect((v) => !v)}>
            {showConnect ? "Close" : "Connect account"}
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

      {selfServiceBlocked ? (
        <ApiNote>
          CU7-002 — self-service connect is disabled by agency policy. Ask your agency to enable
          it or connect on your behalf.
        </ApiNote>
      ) : null}

      {showConnect ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => void onConnect(event)}>
            <FormSelect label="Provider" name="provider" required defaultValue="">
              <option value="" disabled>
                Select provider
              </option>
              {providers.map((row) => (
                <option key={row.provider} value={row.provider}>
                  {row.provider} · {row.category}
                </option>
              ))}
            </FormSelect>
            <FormField label="Display name" name="display_name" required />
            <div className="sm:col-span-2">
              <FormField
                label="Credential / token"
                name="credential"
                type="password"
                required
                autoComplete="off"
              />
            </div>
            <ActionButton type="submit" disabled={busy}>
              Save connection
            </ActionButton>
          </form>
        </article>
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
            Connections ({connections.length})
          </h2>
          {loading ? (
            <p className="m-0 text-body text-text-muted">Loading…</p>
          ) : !connections.length ? (
            <p className="m-0 text-body text-text-muted">No integrations for this customer.</p>
          ) : (
            <ul className="m-0 grid list-none gap-2 p-0">
              {connections.map((row) => (
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
                        {row.display_name || row.provider}
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
          <ApiNote>CU7-001 — show integrations relevant to this customer.</ApiNote>
        </article>

        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">Detail</h2>
          {!selected ? (
            <p className="m-0 text-body text-text-muted">Select a connection.</p>
          ) : (
            <div className="grid gap-3">
              <p className="m-0 text-sm text-text-muted">
                {selected.provider}
                {selected.has_secret ? " · secret stored" : ""}
              </p>
              <ActionButton disabled={busy} onClick={() => void testConnection(selected.id)}>
                Test connection
              </ActionButton>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
