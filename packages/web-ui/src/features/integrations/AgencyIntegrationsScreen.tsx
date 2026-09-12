import { FormEvent, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencyIntegrations } from "./hooks/useAgencyIntegrations";

type Tab = "connections" | "webhooks" | "actions" | "secrets";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "connected" || value === "active" || value === "delivered") return "success";
  if (value === "pending") return "warning";
  if (value === "disabled" || value === "revoked" || value === "failed" || value === "dead") {
    return "danger";
  }
  return "neutral";
}

export function AgencyIntegrationsScreen() {
  const {
    providers,
    connections,
    webhooks,
    deliveries,
    customers,
    selected,
    selectedId,
    setSelectedId,
    customerId,
    setCustomerId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    reload,
    connect,
    testConnection,
    disconnect,
    createWebhook,
    rotateWebhookSecret,
    replayDelivery,
  } = useAgencyIntegrations();

  const [tab, setTab] = useState<Tab>("connections");
  const [showConnect, setShowConnect] = useState(false);
  const [showWebhook, setShowWebhook] = useState(false);
  const [lastSecret, setLastSecret] = useState("");

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
      setTab("secrets");
    } catch {
      /* hook message */
    }
  }

  async function onCreateWebhook(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const events = String(form.get("events") || "call.completed")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    try {
      const created = await createWebhook({
        url: String(form.get("url") || ""),
        events,
      });
      if (created.secret) setLastSecret(created.secret);
      setShowWebhook(false);
      event.currentTarget.reset();
      setTab("secrets");
    } catch {
      /* hook message */
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "connections", label: "Connections" },
    { id: "webhooks", label: "Automations" },
    { id: "actions", label: "Actions" },
    { id: "secrets", label: "Secrets" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Integrations
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Connections, webhooks, actions, secrets · AG8
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowConnect((v) => !v)}>
            {showConnect ? "Close" : "Connect provider"}
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

      <div className="mb-4 grid gap-3 sm:grid-cols-2">
        <FormSelect
          label="Customer"
          name="customer_id"
          value={customerId}
          onChange={(event) => setCustomerId(event.target.value)}
          required
        >
          <option value="" disabled>
            Select customer
          </option>
          {customers.map((row) => (
            <option key={row.id} value={row.id}>
              {row.display_name || row.id.slice(0, 8)}
            </option>
          ))}
        </FormSelect>
        <FormField
          label="Search connections"
          name="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Provider, name, status…"
        />
      </div>

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

      {showConnect ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Connect provider
          </h2>
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
                placeholder="Paste once — never shown again after save"
              />
            </div>
            <ActionButton type="submit" disabled={busy || !customerId}>
              Save connection
            </ActionButton>
          </form>
          <ApiNote>
            AG8-001 / AG8-005 — credentials are stored encrypted and never returned to the UI after
            save.
          </ApiNote>
        </article>
      ) : null}

      {tab === "actions" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Map agent actions
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Agent action → integration mapping is enforced server-side against the provider
            allowlist. A dedicated mapping editor is not yet on the agency API.
          </p>
          <ApiNote>
            AG8-003 — connect CRM/automation providers here; map actions from agent configuration
            when the actions API ships.
          </ApiNote>
        </article>
      ) : tab === "secrets" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Secrets policy
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Stored credentials and webhook signing secrets are never displayed after storage.
            Rotate generates a one-time secret for clipboard copy only.
          </p>
          {lastSecret ? (
            <div className="mb-3 rounded-lg border border-border-default bg-surface-muted px-3 py-2">
              <p className="m-0 text-sm text-text-muted">One-time secret (copy now)</p>
              <code className="break-all text-sm text-text-primary">{lastSecret}</code>
              <div className="mt-2">
                <ActionButton variant="outline" onClick={() => setLastSecret("")}>
                  Clear from screen
                </ActionButton>
              </div>
            </div>
          ) : null}
          <ApiNote>AG8-005 — has_secret indicates presence only; values are never echoed.</ApiNote>
        </article>
      ) : tab === "webhooks" ? (
        <div className="grid gap-4">
          <div className="flex flex-wrap gap-2">
            <ActionButton variant="outline" onClick={() => setShowWebhook((v) => !v)}>
              {showWebhook ? "Close form" : "Add webhook endpoint"}
            </ActionButton>
          </div>
          {showWebhook ? (
            <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
              <form className="grid gap-3" onSubmit={(event) => void onCreateWebhook(event)}>
                <FormField
                  label="Callback URL"
                  name="url"
                  required
                  placeholder="https://hooks.example.com/vokit"
                />
                <FormField
                  label="Events (comma-separated)"
                  name="events"
                  defaultValue="call.completed"
                  placeholder="call.completed,agent.published"
                />
                <ActionButton type="submit" disabled={busy || !customerId}>
                  Create endpoint
                </ActionButton>
              </form>
              <ApiNote>
                AG8-002 — n8n / Zapier / Make connect through webhook endpoints and signed
                deliveries.
              </ApiNote>
            </article>
          ) : null}

          <div className="grid gap-4 lg:grid-cols-2">
            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                Endpoints ({webhooks.length})
              </h2>
              {!webhooks.length ? (
                <p className="m-0 text-body text-text-muted">No webhook endpoints.</p>
              ) : (
                <ul className="m-0 grid list-none gap-2 p-0">
                  {webhooks.map((row) => (
                    <li
                      key={row.id}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                    >
                      <div>
                        <p className="m-0 break-all font-medium text-text-primary">
                          {row.url || row.id.slice(0, 8)}
                        </p>
                        <p className="m-0 text-sm text-text-muted">
                          {(row.events || []).join(", ") || "—"} · {row.status || "—"}
                        </p>
                      </div>
                      <ActionButton
                        variant="outline"
                        disabled={busy}
                        onClick={() => {
                          void rotateWebhookSecret(row.id).then((result) => {
                            if (result?.secret) {
                              setLastSecret(result.secret);
                              setTab("secrets");
                            }
                          });
                        }}
                      >
                        Rotate secret
                      </ActionButton>
                    </li>
                  ))}
                </ul>
              )}
            </article>
            <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
              <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
                Deliveries
              </h2>
              {!deliveries.length ? (
                <p className="m-0 text-body text-text-muted">No deliveries yet.</p>
              ) : (
                <ul className="m-0 grid max-h-[360px] list-none gap-2 overflow-auto p-0">
                  {deliveries.slice(0, 20).map((row) => (
                    <li
                      key={row.id}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                    >
                      <div>
                        <p className="m-0 text-sm font-medium text-text-primary">
                          {row.event_type || row.id.slice(0, 8)}
                        </p>
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "—"}
                        </StatusBadge>
                      </div>
                      {(row.status === "failed" || row.status === "dead") && (
                        <ActionButton
                          variant="outline"
                          disabled={busy}
                          onClick={() => void replayDelivery(row.id)}
                        >
                          Replay
                        </ActionButton>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </div>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
              Connections ({connections.length})
            </h2>
            {!customerId ? (
              <p className="m-0 text-body text-text-muted">Select a customer to load connections.</p>
            ) : loading ? (
              <p className="m-0 text-body text-text-muted" role="status">
                Loading…
              </p>
            ) : !connections.length ? (
              <p className="m-0 text-body text-text-muted">No connections for this customer.</p>
            ) : (
              <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
                {connections.map((row) => (
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
                          {row.display_name || row.provider || row.id.slice(0, 8)}
                        </span>
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "—"}
                        </StatusBadge>
                      </div>
                      <p className="m-0 mt-1 text-sm text-text-muted">
                        {row.provider}
                        {row.has_secret ? " · secret stored" : ""}
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
              Connection detail
            </h2>
            {!selected ? (
              <p className="m-0 text-body text-text-muted">Select a connection.</p>
            ) : (
              <div className="grid gap-3">
                <dl className="m-0 grid gap-2 text-sm">
                  <div>
                    <dt className="text-text-muted">Provider</dt>
                    <dd className="m-0 text-text-primary">{selected.provider}</dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Display name</dt>
                    <dd className="m-0 text-text-primary">{selected.display_name || "—"}</dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Secret</dt>
                    <dd className="m-0 text-text-primary">
                      {selected.has_secret
                        ? "Stored (value hidden)"
                        : "No credential on file"}
                    </dd>
                  </div>
                </dl>
                <div className="flex flex-wrap gap-2">
                  <ActionButton
                    disabled={busy}
                    onClick={() => void testConnection(selected.id)}
                  >
                    Test connection
                  </ActionButton>
                  <ActionButton
                    variant="outline"
                    disabled={busy}
                    onClick={() => {
                      if (window.confirm("Disconnect this integration?")) {
                        void disconnect(selected.id);
                      }
                    }}
                  >
                    Disconnect
                  </ActionButton>
                </div>
                <ApiNote>AG8-004 — test shows success or error without revealing secrets.</ApiNote>
              </div>
            )}
          </article>
        </div>
      )}
    </section>
  );
}
