import { apiGet, apiSend } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { PayoutMethodInput, PayoutMethodRecord } from "@/features/payouts/types";

export async function listAgencyPayoutMethods(filters?: {
  usable?: boolean;
}): Promise<PayoutMethodRecord[]> {
  const params = new URLSearchParams();
  if (filters?.usable) params.set("usable", "true");
  const qs = params.toString();
  return asList<PayoutMethodRecord>(
    await apiGet<unknown>(`/api/v1/agency/payout-methods${qs ? `?${qs}` : ""}`),
  );
}

export async function createAgencyPayoutMethod(
  input: PayoutMethodInput,
): Promise<PayoutMethodRecord> {
  return apiSend<PayoutMethodRecord>("/api/v1/agency/payout-methods", "POST", input);
}

export async function updateAgencyPayoutMethod(
  methodId: string,
  input: Partial<PayoutMethodInput>,
): Promise<PayoutMethodRecord> {
  return apiSend<PayoutMethodRecord>(
    `/api/v1/agency/payout-methods/${methodId}`,
    "PATCH",
    input,
  );
}

export async function disableAgencyPayoutMethod(
  methodId: string,
): Promise<PayoutMethodRecord> {
  return apiSend<PayoutMethodRecord>(
    `/api/v1/agency/payout-methods/${methodId}`,
    "DELETE",
    {},
  );
}

export async function enableAgencyPayoutMethod(
  methodId: string,
): Promise<PayoutMethodRecord> {
  return apiSend<PayoutMethodRecord>(
    `/api/v1/agency/payout-methods/${methodId}`,
    "POST",
    { action: "enable" },
  );
}
