import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList, safeGetList } from "@/features/platform/lib/list";
import type { InboxItem, NotificationDelivery, NotificationTemplate } from "@/features/notifications/types";

export function usePlatformNotifications() {
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  const [deliveries, setDeliveries] = useState<NotificationDelivery[]>([]);
  const [inbox, setInbox] = useState<InboxItem[]>([]);
  const [agencies, setAgencies] = useState<Array<{ id: string; display_name?: string }>>([]);
  const [selectedTemplateKey, setSelectedTemplateKey] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [templateRows, deliveryRows, inboxRows, agencyRows] = await Promise.all([
        asList<NotificationTemplate>(
          await apiGet<unknown>("/api/v1/platform/notification-templates"),
        ),
        asList<NotificationDelivery>(
          await apiGet<unknown>("/api/v1/platform/notification-deliveries"),
        ),
        asList<InboxItem>(await apiGet<unknown>("/api/v1/platform/notifications")),
        safeGetList<{ id: string; display_name?: string }>("/api/v1/platform/agencies", (path) =>
          apiGet(path),
        ),
      ]);
      setTemplates(templateRows);
      setDeliveries(deliveryRows);
      setInbox(inboxRows);
      setAgencies(agencyRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load notifications.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filteredTemplates = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return templates;
    return templates.filter((row) =>
      [row.event_type, row.channel, row.subject, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [templates, query]);

  const selectedTemplate =
    templates.find((row) => `${row.event_type}:${row.channel}` === selectedTemplateKey) ?? null;

  async function saveTemplate(input: {
    event_type: string;
    channel: string;
    subject: string;
    body: string;
    reason: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend("/api/v1/platform/notification-templates", "POST", input);
      setMessage("Template saved (new version).");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Template save failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function sendAnnouncement(input: {
    title: string;
    body: string;
    agency_id?: string;
    reason?: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const payload: Record<string, unknown> = {
        title: input.title,
        body: input.body,
        reason: input.reason || "platform announcement",
      };
      if (input.agency_id) payload.agency_id = input.agency_id;
      const result = await apiSend<{ sent?: number }>("/api/v1/platform/announcements", "POST", payload);
      setMessage(`Announcement dispatched (${result.sent ?? 0} deliveries).`);
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Announcement failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function markRead(notificationId: string) {
    try {
      await apiSend(`/api/v1/platform/notifications/${notificationId}/read`, "POST", {});
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Mark read failed.");
    }
  }

  return {
    templates: filteredTemplates,
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
  };
}
