import { useEffect, useState } from "react";

import {
  DashboardPayload,
  Portal,
  apiGet,
  getDashboard,
  isApiError,
} from "../../../api";

export type CallRow = {
  id: string;
  agency_id?: string;
  customer_id?: string;
  agent_id?: string;
  remote_e164?: string;
  e164?: string;
  direction?: string;
  status?: string;
  billed_minutes?: number;
  duration_seconds?: number;
  started_at?: string | null;
  ended_at?: string | null;
};

export type AgentRow = {
  id: string;
  display_name?: string;
  name?: string;
  status?: string;
  customer_id?: string;
};

export type AgencyRow = {
  id: string;
  display_name?: string;
  status?: string;
};

export type InvoiceRow = {
  id: string;
  status?: string;
  total_minor?: number;
  amount_minor?: number;
  currency?: string;
  created_at?: string;
  paid_at?: string | null;
  due_at?: string | null;
};

export type PayoutRow = {
  id: string;
  status?: string;
  amount_minor?: number;
  tenant_id?: string;
  created_at?: string;
};

export type KycRow = {
  id: string;
  status?: string;
  tenant_id?: string;
  updated_at?: string;
};

export type PaymentMethodRow = {
  id: string;
  brand?: string;
  last4?: string;
  exp_month?: number;
  exp_year?: number;
  is_default?: boolean;
};

function asList<T>(data: unknown): T[] {
  if (Array.isArray(data)) {
    return data as T[];
  }
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    for (const key of [
      "results",
      "items",
      "calls",
      "agents",
      "invoices",
      "payouts",
      "cases",
      "knowledge",
    ]) {
      if (Array.isArray(record[key])) {
        return record[key] as T[];
      }
    }
  }
  return [];
}

async function safeGet<T>(path: string): Promise<T[]> {
  try {
    return asList<T>(await apiGet<unknown>(path));
  } catch {
    return [];
  }
}

export function useDashboardBundle(
  portal: Portal,
  period: string,
  timezone: string,
  range?: { since?: string; until?: string },
) {
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [calls, setCalls] = useState<CallRow[]>([]);
  const [agents, setAgents] = useState<AgentRow[]>([]);
  const [agencies, setAgencies] = useState<AgencyRow[]>([]);
  const [invoices, setInvoices] = useState<InvoiceRow[]>([]);
  const [payouts, setPayouts] = useState<PayoutRow[]>([]);
  const [kycCases, setKycCases] = useState<KycRow[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethodRow[]>([]);
  const [knowledgeCount, setKnowledgeCount] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const since = range?.since;
  const until = range?.until;

  useEffect(() => {
    let active = true;
    setLoading(true);

    const load = async () => {
      const dashboard = await getDashboard(portal, {
        period,
        timezone,
        since: period === "custom" ? since : undefined,
        until: period === "custom" ? until : undefined,
      });
      if (portal === "platform") {
        const [callRows, agentRows, agencyRows, invoiceRows, payoutRows, kycRows] =
          await Promise.all([
            safeGet<CallRow>("/api/v1/platform/calls"),
            safeGet<AgentRow>("/api/v1/platform/agents"),
            safeGet<AgencyRow>("/api/v1/platform/agencies"),
            safeGet<InvoiceRow>("/api/v1/platform/invoices"),
            safeGet<PayoutRow>("/api/v1/platform/payouts"),
            safeGet<KycRow>("/api/v1/platform/kyc/cases"),
          ]);
        if (!active) return;
        setData(dashboard);
        setCalls(callRows);
        setAgents(agentRows);
        setAgencies(agencyRows);
        setInvoices(invoiceRows);
        setPayouts(payoutRows);
        setKycCases(kycRows);
        setPaymentMethods([]);
        setKnowledgeCount(0);
        setError("");
        return;
      }

      if (portal === "agency") {
        const [callRows, agentRows, knowledgeRows] = await Promise.all([
          safeGet<CallRow>("/api/v1/agency/calls"),
          safeGet<AgentRow>("/api/v1/agency/agents"),
          safeGet<{ id: string }>("/api/v1/agency/knowledge"),
        ]);
        if (!active) return;
        setData(dashboard);
        setCalls(callRows);
        setAgents(agentRows);
        setAgencies([]);
        setInvoices([]);
        setPayouts([]);
        setKycCases([]);
        setPaymentMethods([]);
        setKnowledgeCount(knowledgeRows.length);
        setError("");
        return;
      }

      const [invoiceRows, methodRows] = await Promise.all([
        safeGet<InvoiceRow>("/api/v1/customer/invoices"),
        safeGet<PaymentMethodRow>("/api/v1/customer/payment-methods"),
      ]);
      if (!active) return;
      setData(dashboard);
      setCalls([]);
      setAgents([]);
      setAgencies([]);
      setInvoices(invoiceRows);
      setPayouts([]);
      setKycCases([]);
      setPaymentMethods(methodRows);
      setKnowledgeCount(0);
      setError("");
    };

    if (period === "custom" && (!since || !until)) {
      setLoading(false);
      return;
    }

    load()
      .catch((cause) => {
        if (active) {
          setError(isApiError(cause) ? cause.message : "Dashboard failed.");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [portal, period, timezone, since, until]);

  return {
    data,
    calls,
    agents,
    agencies,
    invoices,
    payouts,
    kycCases,
    paymentMethods,
    knowledgeCount,
    error,
    loading,
  };
}
