import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { PhoneNumberRecord } from "@/features/numbers/types";

export type NumberAssignment = {
  id: string;
  number_id?: string;
  e164?: string;
  agency_id?: string;
  customer_id?: string;
  agent_id?: string;
  status?: string;
  invoice_id?: string | null;
  assigned_at?: string;
  released_at?: string | null;
};

export type NumberOffer = {
  e164?: string;
  country?: string;
  area?: string;
  capabilities?: string[];
  monthly_cost_minor?: number;
  provider?: string;
};

export type NumberReservation = {
  id: string;
  number_id?: string;
  agency_id?: string;
  customer_id?: string;
  agent_id?: string;
  status?: string;
  expires_at?: string;
};

export type CustomerOption = {
  id: string;
  display_name?: string;
};

export type AgentOption = {
  id: string;
  display_name?: string;
  customer_id?: string;
  status?: string;
};

function idempotencyKey(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function useAgencyNumbers() {
  const [assigned, setAssigned] = useState<PhoneNumberRecord[]>([]);
  const [assignments, setAssignments] = useState<NumberAssignment[]>([]);
  const [inventory, setInventory] = useState<PhoneNumberRecord[]>([]);
  const [offers, setOffers] = useState<NumberOffer[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [lastReservation, setLastReservation] = useState<NumberReservation | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [customerFilter, setCustomerFilter] = useState("");
  const [searchCountry, setSearchCountry] = useState("US");
  const [searchArea, setSearchArea] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [owned, customerRows, agentRows] = await Promise.all([
        apiGet<Record<string, unknown>>("/api/v1/agency/phone-numbers"),
        apiGet<unknown>("/api/v1/agency/customers").then((data) =>
          asList<CustomerOption>(data),
        ),
        apiGet<unknown>("/api/v1/agency/agents").then((data) => asList<AgentOption>(data)),
      ]);
      setAssigned(asList<PhoneNumberRecord>(owned, ["assigned"]));
      setAssignments(asList<NumberAssignment>(owned, ["assignments"]));
      setCustomers(customerRows);
      setAgents(agentRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load phone numbers.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filteredAssigned = useMemo(() => {
    const q = query.trim().toLowerCase();
    return assigned.filter((row) => {
      if (customerFilter && row.assigned_customer_id !== customerFilter) return false;
      if (!q) return true;
      return [row.e164, row.status, row.provider, row.assigned_agent_id, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [assigned, query, customerFilter]);

  const selected =
    filteredAssigned.find((row) => row.id === selectedId) ??
    assigned.find((row) => row.id === selectedId) ??
    null;

  async function searchNumbers(input?: { country?: string; area?: string }) {
    setBusy(true);
    setMessage("");
    try {
      const params = new URLSearchParams();
      const country = (input?.country ?? searchCountry).trim();
      const area = (input?.area ?? searchArea).trim();
      if (country) params.set("country", country);
      if (area) params.set("area", area);
      params.set("capability", "voice");
      const data = await apiGet<Record<string, unknown>>(
        `/api/v1/agency/phone-numbers/search?${params.toString()}`,
      );
      setInventory(asList<PhoneNumberRecord>(data, ["inventory"]));
      setOffers(asList<NumberOffer>(data, ["offers"]));
      setMessage(
        `Search complete · ${asList(data, ["inventory"]).length} inventory · ${asList(data, ["offers"]).length} provider offers.`,
      );
    } catch (cause) {
      setInventory([]);
      setOffers([]);
      setMessage(isApiError(cause) ? cause.message : "Search failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function reserveNumber(numberId: string, agentId: string) {
    setBusy(true);
    setMessage("");
    try {
      const reserved = await apiSend<NumberReservation>(
        "/api/v1/agency/phone-numbers/reservations",
        "POST",
        { number_id: numberId, agent_id: agentId },
      );
      setLastReservation(reserved);
      setMessage(`Reserved until ${reserved.expires_at ?? "expiry"} · confirm assign next.`);
      await reload();
      return reserved;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Reserve failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function assignReservation(reservationId: string, confirm: boolean) {
    setBusy(true);
    setMessage("");
    try {
      const result = await apiSend<{
        assignment?: NumberAssignment;
        invoice?: { id?: string; total_minor?: number };
      }>(
        "/api/v1/agency/phone-numbers/assignments",
        "POST",
        { reservation_id: reservationId, confirm },
        { "Idempotency-Key": idempotencyKey("number-assign") },
      );
      setMessage(
        confirm
          ? `Number assigned${result.invoice?.id ? ` · invoice ${result.invoice.id.slice(0, 8)}` : ""}.`
          : "Assignment preview ready — confirm to complete purchase.",
      );
      await reload();
      return result;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Assign failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function releaseNumber(numberId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/phone-numbers/${numberId}/release`, "POST", {
        confirm: true,
      });
      setMessage("Number released. Active inbound routing for this DID will stop.");
      if (selectedId === numberId) setSelectedId("");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Release failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  function customerName(customerId?: string | null) {
    if (!customerId) return "—";
    const row = customers.find((item) => item.id === customerId);
    return row?.display_name || customerId.slice(0, 8);
  }

  function agentName(agentId?: string | null) {
    if (!agentId) return "—";
    const row = agents.find((item) => item.id === agentId);
    return row?.display_name || agentId.slice(0, 8);
  }

  return {
    assigned: filteredAssigned,
    assignments,
    inventory,
    offers,
    customers,
    agents,
    lastReservation,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    customerFilter,
    setCustomerFilter,
    searchCountry,
    setSearchCountry,
    searchArea,
    setSearchArea,
    customerName,
    agentName,
    reload,
    searchNumbers,
    reserveNumber,
    assignReservation,
    releaseNumber,
  };
}
