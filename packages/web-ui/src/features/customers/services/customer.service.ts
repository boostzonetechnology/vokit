import { apiGet, apiSend } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type {
  AgencyCreateCustomerInput,
  AgencyOption,
  CreateCustomerInput,
  CustomerRecord,
  CustomerUsage,
  PlanVersionOption,
  SubscriptionChangeResult,
} from "@/features/customers/types";

export async function listPlatformCustomers(filters: {
  agencyId?: string;
  status?: string;
  query?: string;
}): Promise<CustomerRecord[]> {
  const params = new URLSearchParams();
  if (filters.agencyId) params.set("agency_id", filters.agencyId);
  if (filters.status) params.set("status", filters.status);
  if (filters.query?.trim()) params.set("q", filters.query.trim());
  const qs = params.toString();
  const path = qs ? `/api/v1/platform/customers?${qs}` : "/api/v1/platform/customers";
  return asList<CustomerRecord>(await apiGet<unknown>(path));
}

export async function listAgencyOptions(): Promise<AgencyOption[]> {
  try {
    return asList<AgencyOption>(await apiGet<unknown>("/api/v1/platform/agencies"));
  } catch {
    return [];
  }
}

export async function getPlatformCustomer(customerId: string): Promise<CustomerRecord> {
  return apiGet<CustomerRecord>(`/api/v1/platform/customers/${customerId}`);
}

export async function getAgencyCustomer(customerId: string): Promise<CustomerRecord> {
  return apiGet<CustomerRecord>(`/api/v1/agency/customers/${customerId}`);
}

export async function createPlatformCustomer(
  input: CreateCustomerInput,
): Promise<CustomerRecord> {
  return apiSend<CustomerRecord>("/api/v1/platform/customers", "POST", input);
}

export async function createAgencyCustomer(
  input: AgencyCreateCustomerInput,
): Promise<CustomerRecord> {
  return apiSend<CustomerRecord>("/api/v1/agency/customers", "POST", input);
}

export async function setPlatformCustomerStatus(
  customerId: string,
  input: { action: string; reason?: string },
): Promise<CustomerRecord> {
  return apiSend<CustomerRecord>(`/api/v1/platform/customers/${customerId}/status`, "POST", input);
}

export async function setAgencyCustomerStatus(
  customerId: string,
  input: { action: string; reason?: string },
): Promise<CustomerRecord> {
  return apiSend<CustomerRecord>(`/api/v1/agency/customers/${customerId}/status`, "POST", input);
}

export async function getPlatformCustomerUsage(customerId: string): Promise<CustomerUsage | null> {
  try {
    return await apiGet<CustomerUsage>(`/api/v1/platform/customers/${customerId}/usage`);
  } catch {
    return null;
  }
}

export async function adjustPlatformCustomerMinutes(
  customerId: string,
  input: { minutes: number; reason: string },
): Promise<CustomerUsage> {
  return apiSend<CustomerUsage>(
    `/api/v1/platform/customers/${customerId}/minutes-adjustment`,
    "POST",
    input,
  );
}

export async function assignPlatformSubscription(
  customerId: string,
  planVersionId: string,
): Promise<void> {
  await apiSend(`/api/v1/platform/customers/${customerId}/subscription`, "POST", {
    plan_version_id: planVersionId,
  });
}

export async function changePlatformSubscription(
  customerId: string,
  planVersionId: string,
): Promise<SubscriptionChangeResult> {
  return apiSend<SubscriptionChangeResult>(
    `/api/v1/platform/customers/${customerId}/subscription/change`,
    "POST",
    { plan_version_id: planVersionId },
  );
}

export async function assignAgencySubscription(
  customerId: string,
  planVersionId: string,
): Promise<void> {
  await apiSend(`/api/v1/agency/customers/${customerId}/subscription`, "POST", {
    plan_version_id: planVersionId,
  });
}

export async function changeAgencySubscription(
  customerId: string,
  planVersionId: string,
): Promise<SubscriptionChangeResult> {
  return apiSend<SubscriptionChangeResult>(
    `/api/v1/agency/customers/${customerId}/subscription/change`,
    "POST",
    { plan_version_id: planVersionId },
  );
}

export async function listPlatformPlanVersions(): Promise<PlanVersionOption[]> {
  return flattenPlanVersions(await asList<Record<string, unknown>>(await apiGet<unknown>("/api/v1/platform/plans")));
}

export async function listAgencyPlanVersions(): Promise<PlanVersionOption[]> {
  return flattenPlanVersions(await asList<Record<string, unknown>>(await apiGet<unknown>("/api/v1/agency/plans")));
}

function flattenPlanVersions(planRows: Record<string, unknown>[]): PlanVersionOption[] {
  const versions: PlanVersionOption[] = [];
  for (const plan of planRows) {
    const planName = String(plan.name || plan.id || "Plan");
    const planId = String(plan.id || "");
    const nested = asList<Record<string, unknown>>(plan.versions, ["versions", "items"]);
    for (const version of nested) {
      versions.push({
        id: String(version.id),
        plan_id: planId,
        plan_name: planName,
        version: Number(version.version ?? 0),
        price_minor: Number(version.price_minor ?? 0),
        included_minutes: Number(version.included_minutes ?? 0),
        currency: String(version.currency || "USD"),
      });
    }
  }
  return versions;
}

export async function safeListRows<T>(path: string): Promise<T[]> {
  try {
    return asList<T>(await apiGet<unknown>(path));
  } catch {
    return [];
  }
}
