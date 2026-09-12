import { useCallback, useEffect, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { InboxItem } from "@/features/notifications/types";

export type PreferenceRow = {
  event_type: string;
  category?: string;
  mandatory?: boolean;
  email?: boolean;
  in_app?: boolean;
};

export function useAgencySettings() {
  const [preferences, setPreferences] = useState<PreferenceRow[]>([]);
  const [inbox, setInbox] = useState<InboxItem[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [prefRows, inboxRows] = await Promise.all([
        asList<PreferenceRow>(
          await apiGet<unknown>("/api/v1/agency/notification-preferences"),
        ),
        apiGet<unknown>("/api/v1/agency/notifications")
          .then((data) => asList<InboxItem>(data))
          .catch(() => [] as InboxItem[]),
      ]);
      setPreferences(prefRows);
      setInbox(inboxRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load settings.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  function patchPreference(eventType: string, patch: Partial<Pick<PreferenceRow, "email" | "in_app">>) {
    setPreferences((rows) =>
      rows.map((row) => (row.event_type === eventType ? { ...row, ...patch } : row)),
    );
  }

  async function savePreferences() {
    setBusy(true);
    setMessage("");
    try {
      const saved = asList<PreferenceRow>(
        await apiSend<unknown>("/api/v1/agency/notification-preferences", "PUT", {
          preferences: preferences.map((row) => ({
            event_type: row.event_type,
            email: row.email !== false,
            in_app: row.in_app !== false,
          })),
        }),
      );
      setPreferences(saved.length ? saved : preferences);
      setMessage("Notification preferences saved.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Save failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function markRead(notificationId: string) {
    setBusy(true);
    try {
      await apiSend(`/api/v1/agency/notifications/${notificationId}/read`, "POST", {});
      setInbox((rows) =>
        rows.map((row) =>
          row.id === notificationId
            ? { ...row, read_at: row.read_at || new Date().toISOString() }
            : row,
        ),
      );
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Could not mark as read.");
    } finally {
      setBusy(false);
    }
  }

  return {
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
  };
}
