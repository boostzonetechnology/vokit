import { useQuery } from "@tanstack/react-query";

import {
  DashboardPayload,
  Portal,
  apiGet,
  getDashboard,
  isApiError,
} from "@/api";
import {
  DASHBOARD_LISTS_STALE_MS,
  DASHBOARD_SUMMARY_STALE_MS,
  dashboardQueryKeys,
} from "@/features/dashboard/dashboardQueryKeys";

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

type DashboardListsPayload = {
  calls: CallRow[];
  agents: AgentRow[];
  agencies: AgencyRow[];
  invoices: InvoiceRow[];
  payouts: PayoutRow[];
  kycCases: KycRow[];
  paymentMethods: PaymentMethodRow[];
  knowledgeCount: number;
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

function emptyLists(): DashboardListsPayload {
  return {
    calls: [],
    agents: [],
    agencies: [],
    invoices: [],
    payouts: [],
    kycCases: [],
    paymentMethods: [],
    knowledgeCount: 0,
  };
}

async function fetchDashboardLists(portal: Portal): Promise<DashboardListsPayload> {
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
    return {
      calls: callRows,
      agents: agentRows,
      agencies: agencyRows,
      invoices: invoiceRows,
      payouts: payoutRows,
      kycCases: kycRows,
      paymentMethods: [],
      knowledgeCount: 0,
    };
  }

  if (portal === "agency") {
    const [callRows, agentRows, knowledgeRows] = await Promise.all([
      safeGet<CallRow>("/api/v1/agency/calls"),
      safeGet<AgentRow>("/api/v1/agency/agents"),
      safeGet<{ id: string }>("/api/v1/agency/knowledge"),
    ]);
    return {
      calls: callRows,
      agents: agentRows,
      agencies: [],
      invoices: [],
      payouts: [],
      kycCases: [],
      paymentMethods: [],
      knowledgeCount: knowledgeRows.length,
    };
  }

  const [invoiceRows, methodRows, callRows, agentRows] = await Promise.all([
    safeGet<InvoiceRow>("/api/v1/customer/invoices"),
    safeGet<PaymentMethodRow>("/api/v1/customer/payment-methods"),
    safeGet<CallRow>("/api/v1/customer/calls"),
    safeGet<AgentRow>("/api/v1/customer/agents"),
  ]);
  return {
    calls: callRows,
    agents: agentRows,
    agencies: [],
    invoices: invoiceRows,
    payouts: [],
    kycCases: [],
    paymentMethods: methodRows,
    knowledgeCount: 0,
  };
}

export function useDashboardBundle(
  portal: Portal,
  period: string,
  timezone: string,
  range?: { since?: string; until?: string },
) {
  const since = range?.since;
  const until = range?.until;
  const customIncomplete = period === "custom" && (!since || !until);

  const summaryQuery = useQuery<DashboardPayload, Error>({
    queryKey: dashboardQueryKeys.summary(portal, period, timezone, since, until),
    queryFn: () =>
      getDashboard(portal, {
        period,
        timezone,
        since: period === "custom" ? since : undefined,
        until: period === "custom" ? until : undefined,
      }),
    enabled: !customIncomplete,
    staleTime: DASHBOARD_SUMMARY_STALE_MS,
  });

  const listsQuery = useQuery<DashboardListsPayload, Error>({
    queryKey: dashboardQueryKeys.lists(portal),
    queryFn: () => fetchDashboardLists(portal),
    enabled: !customIncomplete,
    staleTime: DASHBOARD_LISTS_STALE_MS,
  });

  const lists = listsQuery.data ?? emptyLists();
  const summaryError = summaryQuery.error
    ? isApiError(summaryQuery.error)
      ? summaryQuery.error.message
      : summaryQuery.error.message || "Dashboard failed."
    : "";
  const listsError = listsQuery.error
    ? isApiError(listsQuery.error)
      ? listsQuery.error.message
      : listsQuery.error.message || "Dashboard lists failed."
    : "";

  const loading =
    !customIncomplete &&
    ((summaryQuery.isPending && !summaryQuery.data) ||
      (listsQuery.isPending && !listsQuery.data));

  return {
    data: summaryQuery.data ?? null,
    calls: lists.calls,
    agents: lists.agents,
    agencies: lists.agencies,
    invoices: lists.invoices,
    payouts: lists.payouts,
    kycCases: lists.kycCases,
    paymentMethods: lists.paymentMethods,
    knowledgeCount: lists.knowledgeCount,
    error: summaryError || listsError,
    loading,
  };
}
