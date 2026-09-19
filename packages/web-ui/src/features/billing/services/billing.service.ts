import { apiGet } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { DisputeRecord, InvoiceRecord, PaymentRecord } from "@/features/billing/types";

export type DirectoryOption = {
  id: string;
  display_name?: string;
};

export async function listPlatformInvoices(filters: {
  status?: string;
}): Promise<InvoiceRecord[]> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  const qs = params.toString();
  return asList<InvoiceRecord>(
    await apiGet<unknown>(`/api/v1/platform/invoices${qs ? `?${qs}` : ""}`),
  );
}

export async function listPlatformPayments(): Promise<PaymentRecord[]> {
  return asList<PaymentRecord>(await apiGet<unknown>("/api/v1/platform/payments"));
}

export async function listPlatformDisputes(): Promise<DisputeRecord[]> {
  return asList<DisputeRecord>(await apiGet<unknown>("/api/v1/platform/disputes"));
}

export async function listBillingAgencies(): Promise<DirectoryOption[]> {
  try {
    return asList<DirectoryOption>(await apiGet<unknown>("/api/v1/platform/agencies"));
  } catch {
    return [];
  }
}

export async function listBillingCustomers(): Promise<DirectoryOption[]> {
  try {
    return asList<DirectoryOption>(await apiGet<unknown>("/api/v1/platform/customers"));
  } catch {
    return [];
  }
}
