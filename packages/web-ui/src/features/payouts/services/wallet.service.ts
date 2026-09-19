import { apiGet, apiSend, apiSendForm } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type {
  AgencyOption,
  LedgerEntry,
  PayoutProof,
  PayoutReceipt,
  PayoutRecord,
  WalletBuckets,
} from "@/features/payouts/types";

function idempotencyKey(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export async function getAgencyWallet(): Promise<{
  buckets: WalletBuckets | null;
  entries: LedgerEntry[];
}> {
  const wallet = await apiGet<{ buckets?: WalletBuckets; entries?: LedgerEntry[] }>(
    "/api/v1/agency/wallet",
  );
  return {
    buckets: wallet.buckets ?? null,
    entries: Array.isArray(wallet.entries) ? wallet.entries : [],
  };
}

export async function listAgencyPayouts(): Promise<PayoutRecord[]> {
  return asList<PayoutRecord>(await apiGet<unknown>("/api/v1/agency/payouts"));
}

export async function requestAgencyPayout(input: {
  amount_minor: number;
  payout_method_id: string;
}): Promise<PayoutRecord> {
  return apiSend<PayoutRecord>(
    "/api/v1/agency/payouts",
    "POST",
    {
      amount_minor: input.amount_minor,
      payout_method_id: input.payout_method_id,
    },
    { "Idempotency-Key": idempotencyKey("payout") },
  );
}

export async function getAgencyPayoutReceipt(payoutId: string): Promise<PayoutReceipt> {
  return apiGet<PayoutReceipt>(`/api/v1/agency/payouts/${payoutId}/receipt`);
}

export async function listPlatformPayouts(filters: {
  status?: string;
}): Promise<PayoutRecord[]> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  const qs = params.toString();
  return asList<PayoutRecord>(
    await apiGet<unknown>(`/api/v1/platform/payouts${qs ? `?${qs}` : ""}`),
  );
}

export async function listPayoutAgencies(): Promise<AgencyOption[]> {
  try {
    return asList<AgencyOption>(await apiGet<unknown>("/api/v1/platform/agencies"));
  } catch {
    return [];
  }
}

export async function getPlatformAgencyWallet(agencyId: string): Promise<WalletBuckets | null> {
  const data = await apiGet<{ buckets?: WalletBuckets }>(
    `/api/v1/platform/agencies/${agencyId}/wallet`,
  );
  return data.buckets ?? null;
}

export async function runPlatformPayoutAction(
  payoutId: string,
  input: { action: string; transaction_ref?: string },
): Promise<PayoutRecord> {
  return apiSend<PayoutRecord>(`/api/v1/platform/payouts/${payoutId}/action`, "POST", {
    action: input.action,
    transaction_ref: input.transaction_ref ?? "",
  });
}

export async function markPlatformPayoutPaid(
  payoutId: string,
  transaction_ref: string,
): Promise<PayoutRecord> {
  return apiSend<PayoutRecord>(`/api/v1/platform/payouts/${payoutId}/mark-paid`, "POST", {
    transaction_ref,
  });
}

export async function uploadPlatformPayoutProof(
  payoutId: string,
  file: File,
  agencyVisible = false,
): Promise<PayoutProof> {
  const form = new FormData();
  form.append("file", file);
  if (agencyVisible) form.append("agency_visible", "true");
  return apiSendForm<PayoutProof>(`/api/v1/platform/payouts/${payoutId}/proof`, form);
}

export async function getPlatformPayoutProof(payoutId: string): Promise<PayoutProof | null> {
  try {
    return await apiGet<PayoutProof>(`/api/v1/platform/payouts/${payoutId}/proof`);
  } catch {
    return null;
  }
}

export function platformPayoutProofFileUrl(payoutId: string): string {
  return `/api/v1/platform/payouts/${payoutId}/proof/file`;
}

export async function setPlatformPayoutProofAgencyVisible(
  payoutId: string,
  agencyVisible: boolean,
): Promise<PayoutProof> {
  return apiSend<PayoutProof>(`/api/v1/platform/payouts/${payoutId}/proof`, "PATCH", {
    agency_visible: agencyVisible,
  });
}

export async function getAgencyPayoutProof(payoutId: string): Promise<PayoutProof | null> {
  try {
    return await apiGet<PayoutProof>(`/api/v1/agency/payouts/${payoutId}/proof`);
  } catch {
    return null;
  }
}

export function agencyPayoutProofFileUrl(payoutId: string): string {
  return `/api/v1/agency/payouts/${payoutId}/proof/file`;
}

export async function adjustAgencyWallet(input: {
  agencyId: string;
  amount_minor: number;
  direction: string;
  reason: string;
}): Promise<void> {
  await apiSend(`/api/v1/platform/agencies/${input.agencyId}/wallet/adjust`, "POST", {
    amount_minor: input.amount_minor,
    direction: input.direction,
    reason: input.reason,
  });
}

export async function freezeAgencyWallet(input: {
  agencyId: string;
  frozen: boolean;
  reason: string;
}): Promise<void> {
  await apiSend(`/api/v1/platform/agencies/${input.agencyId}/wallet/freeze`, "POST", {
    frozen: input.frozen,
    reason: input.reason,
  });
}
