import { useCallback, useEffect, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { InboxItem } from "@/features/notifications/types";

/** Lightweight platform inbox for the top-bar panel (not the full notifications screen). */
export function usePlatformInbox(enabled: boolean) {
  const [inbox, setInbox] = useState<InboxItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError("");
    try {
      setInbox(asList<InboxItem>(await apiGet<unknown>("/api/v1/platform/notifications")));
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load notifications.");
      setInbox([]);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) return;
    void reload();
  }, [enabled, reload]);

  async function markRead(notificationId: string) {
    await apiSend(`/api/v1/platform/notifications/${notificationId}/read`, "POST", {});
    setInbox((rows) =>
      rows.map((row) =>
        row.id === notificationId ? { ...row, read_at: row.read_at || new Date().toISOString() } : row,
      ),
    );
  }

  const unreadCount = inbox.reduce((count, row) => (row.read_at ? count : count + 1), 0);

  return { inbox, loading, error, unreadCount, reload, markRead };
}
