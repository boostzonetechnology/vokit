export type InvoiceLine = {
  description?: string;
  amount_minor?: number;
  quantity?: number;
  commissionable?: boolean;
};

export type InvoiceRecord = {
  id: string;
  agency_id?: string;
  customer_id?: string;
  status?: string;
  currency?: string;
  total_minor?: number;
  paid_at?: string | null;
  lines?: InvoiceLine[];
};

export type PaymentRecord = {
  id: string;
  invoice_id?: string;
  agency_id?: string;
  customer_id?: string;
  processor?: string;
  amount_minor?: number;
  currency?: string;
  status?: string;
};

export type DisputeRecord = {
  processor?: string;
  event_id?: string;
  customer_id?: string | null;
  kind?: string;
  status?: string;
};

export type BillingTab = "payments" | "invoices" | "refunds" | "disputes" | "adjustments";
