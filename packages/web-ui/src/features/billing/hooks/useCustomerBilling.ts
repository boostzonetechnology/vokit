import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import type { InvoiceRecord } from "@/features/billing/types";
import { asList } from "@/features/platform/lib/list";

export type UsageLot = {
  id: string;
  kind?: string;
  granted_minutes?: number;
  remaining_minutes?: number;
};

export type UsagePayload = {
  remaining_minutes?: number;
  drain_order?: string[];
  overage_enabled?: boolean;
  grace_seconds?: number;
  lots?: UsageLot[];
};

export type PayIntent = {
  invoice_id?: string;
  processor?: string;
  amount_minor?: number;
  currency?: string;
  client_reference?: string;
  status?: string;
};

export type PaymentMethodRow = {
  id: string;
  brand?: string;
  last4?: string;
  exp_month?: number;
  exp_year?: number;
  is_default?: boolean;
};

function idempotencyKey(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function useCustomerBilling() {
  const [usage, setUsage] = useState<UsagePayload | null>(null);
  const [invoices, setInvoices] = useState<InvoiceRecord[]>([]);
  const [methods, setMethods] = useState<PaymentMethodRow[]>([]);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [payIntent, setPayIntent] = useState<PayIntent | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [query, setQuery] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [usageData, invoiceRows, methodRows] = await Promise.all([
        apiGet<UsagePayload>("/api/v1/customer/usage"),
        asList<InvoiceRecord>(await apiGet<unknown>("/api/v1/customer/invoices")),
        apiGet<unknown>("/api/v1/customer/payment-methods")
          .then((data) => asList<PaymentMethodRow>(data))
          .catch(() => [] as PaymentMethodRow[]),
      ]);
      setUsage(usageData);
      setInvoices(invoiceRows);
      setMethods(methodRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load billing.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filteredInvoices = useMemo(() => {
    const q = query.trim().toLowerCase();
    return invoices.filter((row) => {
      if (statusFilter && (row.status ?? "").toLowerCase() !== statusFilter) return false;
      if (!q) return true;
      return [row.id, row.status, String(row.total_minor ?? "")]
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [invoices, query, statusFilter]);

  const selectedInvoice =
    filteredInvoices.find((row) => row.id === selectedInvoiceId) ??
    invoices.find((row) => row.id === selectedInvoiceId) ??
    null;

  const usageSummary = useMemo(() => {
    const lots = usage?.lots ?? [];
    const granted = lots.reduce((sum, lot) => sum + (lot.granted_minutes ?? 0), 0);
    const remaining = usage?.remaining_minutes ?? lots.reduce(
      (sum, lot) => sum + (lot.remaining_minutes ?? 0),
      0,
    );
    const consumed = Math.max(0, granted - remaining);
    const included = lots
      .filter((lot) => (lot.kind ?? "").toLowerCase().includes("included"))
      .reduce((sum, lot) => sum + (lot.remaining_minutes ?? 0), 0);
    const additional = lots
      .filter((lot) => !(lot.kind ?? "").toLowerCase().includes("included"))
      .reduce((sum, lot) => sum + (lot.remaining_minutes ?? 0), 0);
    return { granted, remaining, consumed, included, additional, lots };
  }, [usage]);

  async function topUp() {
    setBusy(true);
    setMessage("");
    try {
      const invoice = await apiSend<InvoiceRecord>(
        "/api/v1/customer/usage/top-ups",
        "POST",
        {},
        { "Idempotency-Key": idempotencyKey("topup") },
      );
      setMessage(
        invoice.id
          ? `Top-up invoice created (${invoice.id.slice(0, 8)}).`
          : "Top-up package purchased.",
      );
      await reload();
      if (invoice.id) setSelectedInvoiceId(invoice.id);
      return invoice;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Top-up failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function payInvoice(invoiceId: string, processor = "stripe") {
    setBusy(true);
    setMessage("");
    try {
      const intent = await apiSend<PayIntent>(
        `/api/v1/customer/invoices/${invoiceId}/pay`,
        "POST",
        { processor },
        { "Idempotency-Key": idempotencyKey("pay") },
      );
      setPayIntent(intent);
      setMessage(
        intent.status === "awaiting_webhook"
          ? "Payment initiated — waiting for processor confirmation."
          : "Payment submitted.",
      );
      await reload();
      return intent;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Payment failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  function downloadInvoiceJson(invoice: InvoiceRecord) {
    const blob = new Blob([JSON.stringify(invoice, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `invoice-${invoice.id.slice(0, 8)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    setMessage("Invoice receipt downloaded.");
  }

  return {
    usage,
    usageSummary,
    invoices: filteredInvoices,
    methods,
    selectedInvoice,
    selectedInvoiceId,
    setSelectedInvoiceId,
    payIntent,
    error,
    message,
    loading,
    busy,
    statusFilter,
    setStatusFilter,
    query,
    setQuery,
    reload,
    topUp,
    payInvoice,
    downloadInvoiceJson,
  };
}
