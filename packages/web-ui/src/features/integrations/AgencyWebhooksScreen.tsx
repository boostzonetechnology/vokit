import { FormEvent, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import {
  WEBHOOK_EVENT_TYPES,
  useAgencyWebhooks,
} from "./hooks/useAgencyWebhooks";

type Tab = "endpoints" | "events" | "deliveries" | "secrets" | "test";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active" || value === "delivered") return "success";
  if (value === "pending") return "warning";
  if (value === "disabled" || value === "failed" || value === "dead") return "danger";
  return "neutral";
}

export function AgencyWebhooksScreen() {
  const {
    endpoints,
    deliveries,
    customers,
    customerId,
    setCustomerId,
    selected,
    selectedId,
    setSelectedId,
    lastSecret,
    setLastSecret,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    reload,
    createEndpoint,
    rotateSecret,
    replayDelivery,
  } = useAgencyWebhooks();

  const [tab, setTab] = useState<Tab>("endpoints");
  const [showCreate, setShowCreate] = useState(false);
  const [selectedEvents, setSelectedEvents] = useState<string[]>(["call.completed"]);

  const eventPreview = useMemo(
    () => WEBHOOK_EVENT_TYPES.slice(0, 12),
    [],
  );

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createEndpoint({
        url: String(form.get("url") || ""),
        events: selectedEvents,
      });
      setShowCreate(false);
      event.currentTarget.reset();
      setTab("secrets");
    } catch {
      /* hook message */
    }
  }

  function toggleEvent(eventType: string) {
    setSelectedEvents((current) =>
      current.includes(eventType)
        ? current.filter((item) => item !== eventType)
        : [...current, eventType],
    );
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "endpoints", label: "Endpoints" },
    { id: "events", label: "Events" },
    { id: "deliveries", label: "Delivery log" },
    { id: "secrets", label: "Signing secret" },
    { id: "test", label: "Test event" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Webhooks
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Endpoints, events, secrets, deliveries · AG9
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void reload()}>
            Refresh
          </ActionButton>
          <ActionButton variant="outline" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "Close form" : "Create endpoint"}
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
          label="Search"
          name="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="URL, event, status…"
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

      {showCreate ? (
        <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Create endpoint
          </h2>
          <form className="grid gap-3" onSubmit={(event) => void onCreate(event)}>
            <FormField
              label="Callback URL"
              name="url"
              required
              placeholder="https://hooks.example.com/vokit"
            />
            <fieldset className="m-0 rounded-xl border border-border-default p-3">
              <legend className="px-1 text-sm text-text-muted">Subscribe to events</legend>
              <div className="grid max-h-48 gap-1 overflow-auto sm:grid-cols-2">
                {WEBHOOK_EVENT_TYPES.map((eventType) => (
                  <label key={eventType} className="flex items-center gap-2 text-sm text-text-primary">
                    <input
                      type="checkbox"
                      checked={selectedEvents.includes(eventType)}
                      onChange={() => toggleEvent(eventType)}
                    />
                    {eventType}
                  </label>
                ))}
              </div>
            </fieldset>
            <ActionButton type="submit" disabled={busy || !customerId || !selectedEvents.length}>
              Create endpoint
            </ActionButton>
          </form>
          <ApiNote>
            AG9-001 / AG9-002 — create with allowed event types. Update/disable endpoints are not
            yet on the agency API.
          </ApiNote>
        </article>
      ) : null}

      {tab === "events" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Allowed event catalog
          </h2>
          <ul className="m-0 grid list-none gap-1 p-0 sm:grid-cols-2">
            {eventPreview.map((eventType) => (
              <li key={eventType} className="rounded-lg border border-border-default px-3 py-2 text-sm">
                {eventType}
              </li>
            ))}
          </ul>
          <p className="mt-3 mb-0 text-sm text-text-muted">
            Full catalog has {WEBHOOK_EVENT_TYPES.length} allowed types. Select them when creating
            an endpoint.
          </p>
        </article>
      ) : tab === "secrets" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Signing secret
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Secrets are shown once on create/rotate. Stored secrets are never returned again
            (AG9-003).
          </p>
          {lastSecret ? (
            <div className="mb-3 rounded-lg border border-border-default bg-surface-muted px-3 py-2">
              <p className="m-0 text-sm text-text-muted">One-time secret</p>
              <code className="break-all text-sm text-text-primary">{lastSecret}</code>
              <div className="mt-2">
                <ActionButton variant="outline" onClick={() => setLastSecret("")}>
                  Clear from screen
                </ActionButton>
              </div>
            </div>
          ) : null}
          {selected ? (
            <ActionButton
              disabled={busy}
              onClick={() => void rotateSecret(selected.id).then(() => setTab("secrets"))}
            >
              Rotate secret for selected endpoint
            </ActionButton>
          ) : (
            <p className="m-0 text-body text-text-muted">Select an endpoint to rotate its secret.</p>
          )}
        </article>
      ) : tab === "test" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">Test event</h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            A safe sample/test event sender is not yet exposed on the agency webhook API.
          </p>
          <ApiNote>
            AG9-005 — until a test endpoint ships, use delivery replay on a failed sample or
            trigger a non-destructive event in a sandbox customer.
          </ApiNote>
        </article>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
              {tab === "deliveries" ? "Delivery log" : `Endpoints (${endpoints.length})`}
            </h2>
            {loading ? (
              <p className="m-0 text-body text-text-muted" role="status">
                Loading…
              </p>
            ) : tab === "deliveries" ? (
              !deliveries.length ? (
                <p className="m-0 text-body text-text-muted">No deliveries yet.</p>
              ) : (
                <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
                  {deliveries.map((row) => (
                    <li
                      key={row.id}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                    >
                      <div>
                        <p className="m-0 text-sm font-medium text-text-primary">
                          {row.event_type || row.id.slice(0, 8)}
                        </p>
                        <p className="m-0 text-sm text-text-muted">
                          attempt {row.attempt_count ?? 0}
                          {row.response_code != null ? ` · HTTP ${row.response_code}` : ""} ·{" "}
                          {row.status || "—"}
                        </p>
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
              )
            ) : !endpoints.length ? (
              <p className="m-0 text-body text-text-muted">No endpoints for this customer.</p>
            ) : (
              <ul className="m-0 grid max-h-[520px] list-none gap-2 overflow-auto p-0">
                {endpoints.map((row) => (
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
                        <span className="break-all font-medium text-text-primary">
                          {row.url || row.id.slice(0, 8)}
                        </span>
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "—"}
                        </StatusBadge>
                      </div>
                      <p className="m-0 mt-1 text-sm text-text-muted">
                        {(row.events || []).slice(0, 3).join(", ") || "No events"}
                        {(row.events?.length ?? 0) > 3 ? "…" : ""}
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
            <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">Detail</h2>
            {!selected ? (
              <p className="m-0 text-body text-text-muted">Select an endpoint.</p>
            ) : (
              <div className="grid gap-3">
                <dl className="m-0 grid gap-2 text-sm">
                  <div>
                    <dt className="text-text-muted">URL</dt>
                    <dd className="m-0 break-all text-text-primary">{selected.url}</dd>
                  </div>
                  <div>
                    <dt className="text-text-muted">Events</dt>
                    <dd className="m-0 text-text-primary">
                      {(selected.events || []).join(", ") || "—"}
                    </dd>
                  </div>
                </dl>
                <div className="flex flex-wrap gap-2">
                  <ActionButton
                    variant="outline"
                    disabled={busy}
                    onClick={() => void rotateSecret(selected.id)}
                  >
                    Rotate secret
                  </ActionButton>
                  <ActionButton variant="outline" onClick={() => setTab("deliveries")}>
                    View deliveries
                  </ActionButton>
                </div>
                <ApiNote>
                  AG9-004 — delivery log shows status, response code, retry attempt count. Timestamp
                  fields arrive when the API includes them.
                </ApiNote>
              </div>
            )}
          </article>
        </div>
      )}
    </section>
  );
}
