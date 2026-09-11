import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { DisputeRecord, InvoiceRecord, PaymentRecord } from "@/features/billing/types";

export function usePlatformBilling() {
  const [invoices, setInvoices] = useState<InvoiceRecord[]>([]);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [disputes, setDisputes] = useState<DisputeRecord[]>([]);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [selectedPaymentId, setSelectedPaymentId] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [invoiceStatus, setInvoiceStatus] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const invoiceParams = new URLSearchParams();
      if (invoiceStatus) invoiceParams.set("status", invoiceStatus);
      const invoiceQs = invoiceParams.toString();

      const [invoiceRows, paymentRows, disputeRows] = await Promise.all([
        asList<InvoiceRecord>(
          await apiGet<unknown>(
            `/api/v1/platform/invoices${invoiceQs ? `?${invoiceQs}` : ""}`,
          ),
        ),
        asList<PaymentRecord>(await apiGet<unknown>("/api/v1/platform/payments")),
        asList<DisputeRecord>(await apiGet<unknown>("/api/v1/platform/disputes")),
      ]);
      setInvoices(invoiceRows);
      setPayments(paymentRows);
      setDisputes(disputeRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load billing data.");
    } finally {
      setLoading(false);
    }
  }, [invoiceStatus]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filteredInvoices = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return invoices;
    return invoices.filter((row) =>
      [row.id, row.status, row.customer_id, row.agency_id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [invoices, query]);

  const filteredPayments = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return payments;
    return payments.filter((row) =>
      [row.id, row.status, row.processor, row.invoice_id, row.customer_id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [payments, query]);

  const filteredDisputes = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return disputes;
    return disputes.filter((row) =>
      [row.event_id, row.status, row.kind, row.processor, row.customer_id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [disputes, query]);

  const selectedInvoice = invoices.find((row) => row.id === selectedInvoiceId) ?? null;
  const selectedPayment = payments.find((row) => row.id === selectedPaymentId) ?? null;

  return {
    invoices: filteredInvoices,
    payments: filteredPayments,
    disputes: filteredDisputes,
    selectedInvoice,
    selectedPayment,
    selectedInvoiceId,
    setSelectedInvoiceId,
    selectedPaymentId,
    setSelectedPaymentId,
    error,
    loading,
    query,
    setQuery,
    invoiceStatus,
    setInvoiceStatus,
    reload,
  };
}
