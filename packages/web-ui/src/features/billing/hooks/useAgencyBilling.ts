import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import type { InvoiceRecord } from "@/features/billing/types";
import { asList } from "@/features/platform/lib/list";
import type { PlanRecord } from "@/features/plans/types";

export type CustomerOption = {
  id: string;
  display_name?: string;
};

export function useAgencyBilling() {
  const [plans, setPlans] = useState<PlanRecord[]>([]);
  const [invoices, setInvoices] = useState<InvoiceRecord[]>([]);
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [customerFilter, setCustomerFilter] = useState("");
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (customerFilter) params.set("customer_id", customerFilter);
      const qs = params.toString();
      const [planRows, invoiceRows, customerRows] = await Promise.all([
        asList<PlanRecord>(await apiGet<unknown>("/api/v1/agency/plans")),
        asList<InvoiceRecord>(
          await apiGet<unknown>(`/api/v1/agency/customer-invoices${qs ? `?${qs}` : ""}`),
        ),
        apiGet<unknown>("/api/v1/agency/customers")
          .then((data) => asList<CustomerOption>(data))
          .catch(() => [] as CustomerOption[]),
      ]);
      setPlans(planRows);
      setInvoices(invoiceRows);
      setCustomers(customerRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load billing data.");
    } finally {
      setLoading(false);
    }
  }, [customerFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filteredInvoices = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return invoices;
    return invoices.filter((row) =>
      [row.id, row.status, row.customer_id, String(row.total_minor ?? "")]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [invoices, query]);

  const selectedInvoice =
    filteredInvoices.find((row) => row.id === selectedInvoiceId) ??
    invoices.find((row) => row.id === selectedInvoiceId) ??
    null;

  const selectedPlan = plans.find((row) => row.id === selectedPlanId) ?? null;

  const revenue = useMemo(() => {
    let gross = 0;
    let commissionable = 0;
    for (const invoice of invoices) {
      const currency = invoice.currency || "USD";
      void currency;
      for (const line of invoice.lines ?? []) {
        const amount = line.amount_minor ?? 0;
        gross += amount;
        if (line.commissionable) commissionable += amount;
      }
      if (!invoice.lines?.length) {
        gross += invoice.total_minor ?? 0;
      }
    }
    return { gross_minor: gross, commissionable_minor: commissionable };
  }, [invoices]);

  async function assignPlan(customerId: string, planVersionId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/customers/${customerId}/subscription`, "POST", {
        plan_version_id: planVersionId,
      });
      setMessage("Plan assigned — invoice created for the customer.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Plan assignment failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  function customerName(customerId?: string) {
    if (!customerId) return "—";
    return customers.find((row) => row.id === customerId)?.display_name || customerId.slice(0, 8);
  }

  return {
    plans,
    invoices: filteredInvoices,
    customers,
    customerFilter,
    setCustomerFilter,
    selectedInvoice,
    selectedInvoiceId,
    setSelectedInvoiceId,
    selectedPlan,
    selectedPlanId,
    setSelectedPlanId,
    revenue,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    customerName,
    reload,
    assignPlan,
  };
}
