import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";

export type CustomerOption = {
  id: string;
  display_name?: string;
};

export type WebhookEndpoint = {
  id: string;
  agency_id?: string;
  customer_id?: string;
  url?: string;
  status?: string;
  events?: string[];
  secret?: string;
};

export type WebhookDelivery = {
  id: string;
  endpoint_id?: string;
  event_id?: string;
  event_type?: string;
  object_id?: string;
  customer_id?: string;
  status?: string;
  attempt_count?: number;
  response_code?: number | null;
};

/** Allowed outbound event types (AG9-002) — mirrors backend ALLOWED_EVENT_TYPES. */
export const WEBHOOK_EVENT_TYPES = [
  "agency.created",
  "agency.status.changed",
  "customer.created",
  "customer.status.changed",
  "invoice.created",
  "invoice.paid",
  "payment.failed",
  "commission.created",
  "commission.available",
  "commission.reversed",
  "payout.requested",
  "payout.status.changed",
  "payout.paid",
  "agent.created",
  "agent.published",
  "agent.status.changed",
  "call.started",
  "call.answered",
  "call.completed",
  "call.transcript.ready",
  "call.summary.ready",
  "agent.action.started",
  "agent.action.completed",
  "agent.action.failed",
  "knowledge.updated",
  "phone_number.purchased",
  "phone_number.released",
  "integration.failed",
] as const;

export function useAgencyWebhooks() {
  const [endpoints, setEndpoints] = useState<WebhookEndpoint[]>([]);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [customerId, setCustomerId] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [lastSecret, setLastSecret] = useState("");
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
      setEndpoints([]);
      setDeliveries([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const params = new URLSearchParams({ customer_id: customerId });
      const [endpointRows, deliveryRows] = await Promise.all([
        asList<WebhookEndpoint>(await apiGet<unknown>(`/api/v1/agency/webhooks?${params}`)),
        asList<WebhookDelivery>(
          await apiGet<unknown>(`/api/v1/agency/webhooks/deliveries?${params}`),
        ),
      ]);
      setEndpoints(endpointRows);
      setDeliveries(deliveryRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load webhooks.");
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
    if (!q) return endpoints;
    return endpoints.filter((row) =>
      [row.url, row.status, ...(row.events ?? []), row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [endpoints, query]);

  const selected = endpoints.find((row) => row.id === selectedId) ?? null;

  const selectedDeliveries = useMemo(() => {
    if (!selectedId) return deliveries;
    return deliveries.filter((row) => row.endpoint_id === selectedId);
  }, [deliveries, selectedId]);

  async function createEndpoint(input: { url: string; events: string[] }) {
    if (!customerId) throw new Error("Select a customer first.");
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<WebhookEndpoint>("/api/v1/agency/webhooks", "POST", {
        customer_id: customerId,
        url: input.url,
        events: input.events,
      });
      if (created.secret) setLastSecret(created.secret);
      setMessage(
        created.secret
          ? "Endpoint created. Copy the signing secret now — it will not be shown again."
          : "Endpoint created.",
      );
      await reload();
      if (created.id) setSelectedId(created.id);
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function rotateSecret(endpointId: string) {
    setBusy(true);
    setMessage("");
    try {
      const result = await apiSend<WebhookEndpoint>(
        `/api/v1/agency/webhooks/${endpointId}/rotate`,
        "POST",
        {},
      );
      if (result.secret) setLastSecret(result.secret);
      setMessage(
        result.secret
          ? "Signing secret rotated. Copy the new secret now."
          : "Signing secret rotated.",
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
    endpoints: filtered,
    deliveries: selectedDeliveries,
    allDeliveries: deliveries,
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
  };
}
