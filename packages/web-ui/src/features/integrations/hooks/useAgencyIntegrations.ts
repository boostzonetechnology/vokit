import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { IntegrationConnection, IntegrationProvider } from "@/features/integrations/types";

export type CustomerOption = {
  id: string;
  display_name?: string;
};

export type WebhookEndpoint = {
  id: string;
  customer_id?: string;
  url?: string;
  events?: string[];
  status?: string;
  secret?: string;
  has_secret?: boolean;
};

export type WebhookDelivery = {
  id: string;
  endpoint_id?: string;
  event_type?: string;
  status?: string;
  attempts?: number;
  created_at?: string;
};

export const AGENCY_PROVIDERS: IntegrationProvider[] = [
  { provider: "hubspot", category: "crm" },
  { provider: "salesforce", category: "crm" },
  { provider: "zoho", category: "crm" },
  { provider: "quickbooks", category: "accounting" },
  { provider: "n8n", category: "automation" },
  { provider: "zapier", category: "automation" },
  { provider: "make", category: "automation" },
  { provider: "generic_webhook", category: "automation" },
];

export function useAgencyIntegrations() {
  const [connections, setConnections] = useState<IntegrationConnection[]>([]);
  const [webhooks, setWebhooks] = useState<WebhookEndpoint[]>([]);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");

  const reloadCustomers = useCallback(async () => {
    try {
      const rows = asList<CustomerOption>(await apiGet<unknown>("/api/v1/agency/customers"));
      setCustomers(rows);
      if (!customerId && rows[0]?.id) setCustomerId(rows[0].id);
    } catch {
      setCustomers([]);
    }
  }, [customerId]);

  const reload = useCallback(async () => {
    if (!customerId) {
      setConnections([]);
      setWebhooks([]);
      setDeliveries([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const params = new URLSearchParams({ customer_id: customerId });
      const [connectionRows, webhookRows, deliveryRows] = await Promise.all([
        apiGet<unknown>(`/api/v1/agency/integrations?${params}`).then((data) =>
          asList<IntegrationConnection>(data),
        ),
        apiGet<unknown>(`/api/v1/agency/webhooks?${params}`)
          .then((data) => asList<WebhookEndpoint>(data))
          .catch(() => [] as WebhookEndpoint[]),
        apiGet<unknown>(`/api/v1/agency/webhooks/deliveries?${params}`)
          .then((data) => asList<WebhookDelivery>(data))
          .catch(() => [] as WebhookDelivery[]),
      ]);
      setConnections(connectionRows);
      setWebhooks(webhookRows);
      setDeliveries(deliveryRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load integrations.");
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  useEffect(() => {
    void reloadCustomers();
  }, [reloadCustomers]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return connections;
    return connections.filter((row) =>
      [row.provider, row.display_name, row.status, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [connections, query]);

  const selected = connections.find((row) => row.id === selectedId) ?? null;

  async function connect(input: {
    provider: string;
    credential: string;
    display_name: string;
  }) {
    if (!customerId) throw new Error("Select a customer first.");
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<IntegrationConnection>("/api/v1/agency/integrations", "POST", {
        customer_id: customerId,
        provider: input.provider,
        credential: input.credential,
        display_name: input.display_name,
      });
      setMessage(
        "Connection saved. Credential is stored encrypted and will not be shown again.",
      );
      await reload();
      if (created.id) setSelectedId(created.id);
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Connect failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function testConnection(connectionId: string) {
    setBusy(true);
    setMessage("");
    try {
      const result = await apiSend<{ ok?: boolean; error?: string; status?: string }>(
        `/api/v1/agency/integrations/${connectionId}/test`,
        "POST",
        {},
      );
      setMessage(
        result.ok === false || result.error
          ? `Test failed: ${result.error || result.status || "unknown error"}`
          : "Connection test succeeded.",
      );
      return result;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Test failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function disconnect(connectionId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/integrations/${connectionId}/disconnect`, "POST", {});
      setMessage("Connection disconnected.");
      if (selectedId === connectionId) setSelectedId("");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Disconnect failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function createWebhook(input: { url: string; events: string[] }) {
    if (!customerId) throw new Error("Select a customer first.");
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<WebhookEndpoint>("/api/v1/agency/webhooks", "POST", {
        customer_id: customerId,
        url: input.url,
        events: input.events,
      });
      setMessage(
        created.secret
          ? "Webhook created. Copy the signing secret now — it will not be shown again."
          : "Webhook endpoint created.",
      );
      await reload();
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Webhook create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function rotateWebhookSecret(endpointId: string) {
    setBusy(true);
    setMessage("");
    try {
      const result = await apiSend<WebhookEndpoint>(
        `/api/v1/agency/webhooks/${endpointId}/rotate`,
        "POST",
        {},
      );
      setMessage(
        result.secret
          ? "Secret rotated. Copy the new signing secret now."
          : "Webhook secret rotated.",
      );
      await reload();
      return result;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Rotate failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function replayDelivery(deliveryId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/webhooks/deliveries/${deliveryId}/replay`, "POST", {});
      setMessage("Delivery replay queued.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Replay failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    providers: AGENCY_PROVIDERS,
    connections: filtered,
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
  };
}
