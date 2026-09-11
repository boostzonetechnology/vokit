import { FormEvent, useEffect, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { usePlatformNotifications } from "./hooks/usePlatformNotifications";
import type { NotificationTab } from "./types";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "sent" || value === "delivered") return "success";
  if (value === "failed") return "danger";
  if (value === "pending") return "warning";
  return "neutral";
}

const TAB_FROM_ROUTE: Record<string, NotificationTab> = {
  notifications: "inbox",
  "notice-templates": "templates",
};

export function PlatformNotificationsScreen({ route = "notifications" }: { route?: string }) {
  const {
    templates,
    deliveries,
    inbox,
    agencies,
    selectedTemplate,
    selectedTemplateKey,
    setSelectedTemplateKey,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    reload,
    saveTemplate,
    sendAnnouncement,
    markRead,
  } = usePlatformNotifications();

  const [tab, setTab] = useState<NotificationTab>(TAB_FROM_ROUTE[route] ?? "templates");

  useEffect(() => {
    setTab(TAB_FROM_ROUTE[route] ?? "templates");
  }, [route]);

  async function onSaveTemplate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await saveTemplate({
        event_type: String(form.get("event_type") || ""),
        channel: String(form.get("channel") || "in_app"),
        subject: String(form.get("subject") || ""),
        body: String(form.get("body") || ""),
        reason: String(form.get("reason") || "template update"),
      });
    } catch {
      /* message in hook */
    }
  }

  async function onAnnounce(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await sendAnnouncement({
        title: String(form.get("title") || ""),
        body: String(form.get("body") || ""),
        agency_id: String(form.get("agency_id") || "") || undefined,
        reason: String(form.get("reason") || ""),
      });
      event.currentTarget.reset();
    } catch {
      /* message in hook */
    }
  }

  const tabs: Array<{ id: NotificationTab; label: string }> = [
    { id: "templates", label: "Templates" },
    { id: "deliveries", label: "Delivery logs" },
    { id: "announcements", label: "Announcements" },
    { id: "inbox", label: "Inbox" },
  ];

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Notifications
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            SA16-001–003 · Permission: notifications.manage
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

      {tab === "templates" ? (
        <>
          <article className="mb-4 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <label className="mb-4 m-0 grid max-w-md gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Search templates</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            {loading ? (
              <p className="m-0 text-body text-text-muted">Loading templates…</p>
            ) : (
              <div className="overflow-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-label uppercase text-text-muted">
                      <th className="border-0 px-2 py-2 text-left">Event</th>
                      <th className="border-0 px-2 py-2 text-left">Channel</th>
                      <th className="border-0 px-2 py-2 text-left">Subject</th>
                      <th className="border-0 px-2 py-2 text-left">Version</th>
                    </tr>
                  </thead>
                  <tbody>
                    {templates.map((row) => {
                      const key = `${row.event_type}:${row.channel}`;
                      return (
                        <tr
                          key={key}
                          className={
                            selectedTemplateKey === key
                              ? "cursor-pointer bg-brand-subtle/40"
                              : "cursor-pointer hover:bg-canvas"
                          }
                          onClick={() => setSelectedTemplateKey(key)}
                        >
                          <td className="px-2 py-3 font-semibold text-text-primary">
                            {row.event_type}
                          </td>
                          <td className="px-2 py-3 text-text-secondary">{row.channel}</td>
                          <td className="px-2 py-3 text-text-secondary">{row.subject}</td>
                          <td className="px-2 py-3 text-text-secondary">{row.version ?? "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </article>
          <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
            <h2 className="m-0 mb-3 text-section text-text-primary">
              {selectedTemplate ? "Edit template" : "Create / update template"}
            </h2>
            <form className="grid gap-3" onSubmit={(event) => void onSaveTemplate(event)}>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="m-0 grid gap-1.5 font-normal">
                  <span className="text-body-sm text-text-muted">Event type</span>
                  <input
                    name="event_type"
                    required
                    defaultValue={selectedTemplate?.event_type || ""}
                    key={`event-${selectedTemplateKey}`}
                    className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                  />
                </label>
                <label className="m-0 grid gap-1.5 font-normal">
                  <span className="text-body-sm text-text-muted">Channel</span>
                  <select
                    name="channel"
                    defaultValue={selectedTemplate?.channel || "in_app"}
                    key={`channel-${selectedTemplateKey}`}
                    className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                  >
                    <option value="in_app">in_app</option>
                    <option value="email">email</option>
                  </select>
                </label>
              </div>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Subject</span>
                <input
                  name="subject"
                  required
                  defaultValue={selectedTemplate?.subject || ""}
                  key={`subject-${selectedTemplateKey}`}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                />
              </label>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Body</span>
                <textarea
                  name="body"
                  required
                  rows={6}
                  defaultValue={selectedTemplate?.body || ""}
                  key={`body-${selectedTemplateKey}`}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 font-mono text-body"
                />
              </label>
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Audit reason</span>
                <input
                  name="reason"
                  defaultValue="template update"
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                />
              </label>
              <div>
                <ActionButton type="submit" disabled={busy}>
                  Save template
                </ActionButton>
              </div>
            </form>
          </article>
        </>
      ) : null}

      {tab === "deliveries" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">
            Delivery logs
            <span className="ml-2 text-body font-normal text-text-muted">
              ({deliveries.length})
            </span>
          </h2>
          {deliveries.length === 0 ? (
            <p className="m-0 text-body text-text-muted">No deliveries yet.</p>
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-label uppercase text-text-muted">
                    <th className="border-0 px-2 py-2 text-left">Event</th>
                    <th className="border-0 px-2 py-2 text-left">Channel</th>
                    <th className="border-0 px-2 py-2 text-left">Status</th>
                    <th className="border-0 px-2 py-2 text-left">Recipient</th>
                    <th className="border-0 px-2 py-2 text-left">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {deliveries.map((row) => (
                    <tr key={row.id}>
                      <td className="px-2 py-3 font-semibold text-text-primary">
                        {row.event_type}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.channel || "—"}</td>
                      <td className="px-2 py-3">
                        <StatusBadge tone={statusTone(row.status)}>
                          {row.status || "unknown"}
                        </StatusBadge>
                      </td>
                      <td className="px-2 py-3 text-text-secondary">
                        {row.recipient_email || row.user_id?.slice(0, 8) || "—"}
                      </td>
                      <td className="px-2 py-3 text-text-secondary">{row.created_at || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      ) : null}

      {tab === "announcements" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">Send announcement</h2>
          <form className="grid max-w-xl gap-3" onSubmit={(event) => void onAnnounce(event)}>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Title</span>
              <input
                name="title"
                required
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Body</span>
              <textarea
                name="body"
                required
                rows={5}
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Target agency (optional)</span>
              <select
                name="agency_id"
                defaultValue=""
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              >
                <option value="">Platform-wide</option>
                {agencies.map((agency) => (
                  <option key={agency.id} value={agency.id}>
                    {agency.display_name || agency.id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </label>
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Reason</span>
              <input
                name="reason"
                defaultValue="platform announcement"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <ActionButton type="submit" disabled={busy}>
              Send announcement
            </ActionButton>
          </form>
          <div className="mt-4">
            <ApiNote>
              Empty agency target sends to platform recipients. Agency id scopes to that tenant.
            </ApiNote>
          </div>
        </article>
      ) : null}

      {tab === "inbox" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-3 text-section text-text-primary">
            Platform inbox
            <span className="ml-2 text-body font-normal text-text-muted">({inbox.length})</span>
          </h2>
          {inbox.length === 0 ? (
            <p className="m-0 text-body text-text-muted">Inbox empty.</p>
          ) : (
            <div className="grid gap-2">
              {inbox.map((item) => (
                <div
                  key={item.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border-default bg-canvas px-3 py-3"
                >
                  <div>
                    <p className="m-0 font-semibold text-text-primary">
                      {item.title || item.id.slice(0, 8)}
                    </p>
                    <p className="mt-1 mb-0 text-body-sm text-text-muted">
                      {item.category || "—"} · {item.created_at || "—"}
                      {item.read_at ? " · read" : " · unread"}
                    </p>
                  </div>
                  {!item.read_at ? (
                    <ActionButton variant="outline" onClick={() => void markRead(item.id)}>
                      Mark read
                    </ActionButton>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </article>
      ) : null}
    </section>
  );
}
