import { useCallback, useEffect, useMemo, useState } from "react";

import { isApiError } from "@/api";
import { nameOrId } from "@/features/billing/lib/display";
import {
  listBillingAgencies,
  listBillingCustomers,
  listPlatformDisputes,
  listPlatformInvoices,
  listPlatformPayments,
} from "@/features/billing/services/billing.service";
import type { DisputeRecord, InvoiceRecord, PaymentRecord } from "@/features/billing/types";

export function usePlatformBilling() {
  const [invoices, setInvoices] = useState<InvoiceRecord[]>([]);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [disputes, setDisputes] = useState<DisputeRecord[]>([]);
  const [agencyNames, setAgencyNames] = useState<Map<string, string>>(new Map());
  const [customerNames, setCustomerNames] = useState<Map<string, string>>(new Map());
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [selectedPaymentId, setSelectedPaymentId] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [invoiceStatus, setInvoiceStatus] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [invoiceRows, paymentRows, disputeRows, agencies, customers] = await Promise.all([
        listPlatformInvoices({ status: invoiceStatus }),
        listPlatformPayments(),
        listPlatformDisputes(),
        listBillingAgencies(),
        listBillingCustomers(),
      ]);
      setInvoices(invoiceRows);
      setPayments(paymentRows);
      setDisputes(disputeRows);
      setAgencyNames(
        new Map(agencies.map((row) => [row.id, nameOrId(row.display_name, row.id)])),
      );
      setCustomerNames(
        new Map(customers.map((row) => [row.id, nameOrId(row.display_name, row.id)])),
      );
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

  const agencyLabel = useCallback(
    (id?: string | null) => (id ? agencyNames.get(id) ?? nameOrId(null, id) : "—"),
    [agencyNames],
  );

  const customerLabel = useCallback(
    (id?: string | null) => (id ? customerNames.get(id) ?? nameOrId(null, id) : "—"),
    [customerNames],
  );

  const filteredInvoices = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return invoices;
    return invoices.filter((row) =>
      [
        row.id,
        row.status,
        row.customer_id,
        row.agency_id,
        customerLabel(row.customer_id),
        agencyLabel(row.agency_id),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [invoices, query, customerLabel, agencyLabel]);

  const filteredPayments = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return payments;
    return payments.filter((row) =>
      [
        row.id,
        row.status,
        row.processor,
        row.invoice_id,
        row.customer_id,
        customerLabel(row.customer_id),
        agencyLabel(row.agency_id),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [payments, query, customerLabel, agencyLabel]);

  const filteredDisputes = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return disputes;
    return disputes.filter((row) =>
      [
        row.event_id,
        row.status,
        row.kind,
        row.processor,
        row.customer_id,
        customerLabel(row.customer_id),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [disputes, query, customerLabel]);

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
    agencyLabel,
    customerLabel,
    error,
    loading,
    query,
    setQuery,
    invoiceStatus,
    setInvoiceStatus,
    reload,
  };
}
