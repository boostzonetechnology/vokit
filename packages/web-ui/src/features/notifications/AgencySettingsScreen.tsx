import { useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import { ApiNote } from "@/features/platform/ux/ApiNote";
import { useAgencySettings } from "./hooks/useAgencySettings";

type Tab = "preferences" | "brand" | "security" | "inbox";

function readTone(readAt?: string | null): BadgeTone {
  return readAt ? "neutral" : "warning";
}

type AgencySettingsScreenProps = {
  initialTab?: Tab;
};

export function AgencySettingsScreen({ initialTab = "preferences" }: AgencySettingsScreenProps) {
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
  } = useAgencySettings();

  const [tab, setTab] = useState<Tab>(initialTab);

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "preferences", label: "Notifications" },
    { id: "inbox", label: "Inbox" },
    { id: "brand", label: "Brand / profile" },
    { id: "security", label: "Security" },
  ];

  return (
    <section className="mx-auto max-w-[1100px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Settings
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Preferences, brand, security · AG14
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
          <ActionButton
            key={item.id}
            variant={tab === item.id ? "secondary" : "outline"}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </ActionButton>
        ))}
      </div>

      {loading ? (
        <p className="text-body text-text-muted" role="status">
          Loading…
        </p>
      ) : tab === "brand" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">
            Brand / profile
          </h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Agency profile and branding fields are not yet editable through an agency settings API.
          </p>
          <ApiNote>AG14-002 (Should) — pending agency profile/branding endpoint.</ApiNote>
        </article>
      ) : tab === "security" ? (
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <h2 className="m-0 mb-2 text-[1.05rem] font-semibold text-text-primary">Security</h2>
          <p className="mt-0 mb-3 text-body text-text-muted">
            Session list, password change and MFA enrollment are not yet exposed for agency
            self-service. Use logout from the account menu to end the current session.
          </p>
          <ApiNote>
            AG14-003 — security management UI will connect when session/password/MFA APIs are
            available.
          </ApiNote>
        </article>
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
                    <p className="m-0 mt-1 text-xs text-text-muted">{row.created_at}</p>
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
            <p className="m-0 text-body text-text-muted">No preference rows returned.</p>
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
                  <label className="flex items-center gap-2 text-sm text-text-primary">
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
                  <label className="flex items-center gap-2 text-sm text-text-primary">
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
          <ApiNote>AG14-001 — agency-level notification preferences; mandatory events stay on.</ApiNote>
        </article>
      )}
    </section>
  );
}

export function AgencyNotificationsScreen() {
  return <AgencySettingsScreen initialTab="inbox" />;
}
