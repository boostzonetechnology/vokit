import { useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useCustomerSettings } from "./hooks/useCustomerSettings";

type Tab = "preferences" | "inbox";

function readTone(readAt?: string | null): BadgeTone {
  return readAt ? "neutral" : "warning";
}

type CustomerSettingsScreenProps = {
  initialTab?: Tab;
};

export function CustomerSettingsScreen({
  initialTab = "preferences",
}: CustomerSettingsScreenProps) {
  const {
    preferences,
    inbox,
    error,
    message,
    loading,
    busy,
    reload,
    patchPreference,
    savePreferences,
    markRead,
  } = useCustomerSettings();

  const [tab, setTab] = useState<Tab>(initialTab);

  return (
    <section className="mx-auto max-w-[1100px]">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Settings
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Notification preferences · CU8-002
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
        <ActionButton
          variant={tab === "preferences" ? "secondary" : "outline"}
          onClick={() => setTab("preferences")}
        >
          Preferences
        </ActionButton>
        <ActionButton
          variant={tab === "inbox" ? "secondary" : "outline"}
          onClick={() => setTab("inbox")}
        >
          Inbox
        </ActionButton>
      </div>

      {loading ? (
        <p className="text-body text-text-muted">Loading…</p>
      ) : tab === "inbox" ? (
        <article className="rounded-xl border border-border-default bg-surface p-4 shadow-subtle">
          <h2 className="m-0 mb-3 text-[1.05rem] font-semibold text-text-primary">
            Inbox ({inbox.length})
          </h2>
          {!inbox.length ? (
            <p className="m-0 text-body text-text-muted">No notifications.</p>
          ) : (
            <ul className="m-0 grid max-h-[560px] list-none gap-2 overflow-auto p-0">
              {inbox.map((row) => (
                <li
                  key={row.id}
                  className="flex flex-wrap items-start justify-between gap-2 rounded-lg border border-border-default px-3 py-2"
                >
                  <div>
                    <div className="mb-1 flex items-center gap-2">
                      <span className="font-medium text-text-primary">{row.title || "Notice"}</span>
                      <StatusBadge tone={readTone(row.read_at)}>
                        {row.read_at ? "Read" : "Unread"}
                      </StatusBadge>
                    </div>
                    <p className="m-0 text-sm text-text-muted">{row.body}</p>
                  </div>
                  {!row.read_at ? (
                    <ActionButton
                      variant="outline"
                      disabled={busy}
                      onClick={() => void markRead(row.id)}
                    >
                      Mark read
                    </ActionButton>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </article>
      ) : (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <h2 className="m-0 text-[1.05rem] font-semibold text-text-primary">
              Notification preferences
            </h2>
            <ActionButton disabled={busy} onClick={() => void savePreferences()}>
              Save preferences
            </ActionButton>
          </div>
          {!preferences.length ? (
            <p className="m-0 text-body text-text-muted">No preference rows.</p>
          ) : (
            <ul className="m-0 grid list-none gap-2 p-0">
              {preferences.map((row) => (
                <li
                  key={row.event_type}
                  className="grid gap-2 rounded-lg border border-border-default px-3 py-2 sm:grid-cols-[1.4fr_auto_auto]"
                >
                  <div>
                    <p className="m-0 font-medium text-text-primary">{row.event_type}</p>
                    <p className="m-0 text-sm text-text-muted">
                      {row.category || "—"}
                      {row.mandatory ? " · mandatory" : ""}
                    </p>
                  </div>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={row.email !== false}
                      disabled={row.mandatory || busy}
                      onChange={(event) =>
                        patchPreference(row.event_type, { email: event.target.checked })
                      }
                    />
                    Email
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={row.in_app !== false}
                      disabled={row.mandatory || busy}
                      onChange={(event) =>
                        patchPreference(row.event_type, { in_app: event.target.checked })
                      }
                    />
                    In-app
                  </label>
                </li>
              ))}
            </ul>
          )}
          <ApiNote>CU8-002 — customer notification preferences; mandatory events stay on.</ApiNote>
        </article>
      )}
    </section>
  );
}

export function CustomerNotificationsScreen() {
  return <CustomerSettingsScreen initialTab="inbox" />;
}
