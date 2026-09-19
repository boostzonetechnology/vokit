import { apiGet, apiSend } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type {
  CustomerOption,
  PlanRecord,
  PlanTermsInput,
  PlanVersion,
} from "@/features/plans/types";

function termsBody(input: PlanTermsInput): Record<string, unknown> {
  return {
    price_minor: input.price_minor,
    included_minutes: input.included_minutes,
    allow_topups: input.allow_topups,
    topup_minutes: input.topup_minutes,
    topup_price_minor: input.topup_price_minor,
    overage_enabled: input.overage_enabled,
    overage_price_per_minute_minor: input.overage_price_per_minute_minor,
    grace_seconds: input.grace_seconds,
    max_agents: input.max_agents,
    max_phone_numbers: input.max_phone_numbers,
    max_concurrency: input.max_concurrency,
    recording_allowed: input.recording_allowed,
    allowed_integrations: input.allowed_integrations,
  };
}

export async function listPlans(): Promise<PlanRecord[]> {
  return asList<PlanRecord>(await apiGet<unknown>("/api/v1/platform/plans"));
}

export async function listCustomerOptions(): Promise<CustomerOption[]> {
  try {
    return asList<CustomerOption>(await apiGet<unknown>("/api/v1/platform/customers"));
  } catch {
    return [];
  }
}

export async function createPlan(
  input: PlanTermsInput & { name: string },
): Promise<PlanRecord> {
  return apiSend<PlanRecord>("/api/v1/platform/plans", "POST", {
    name: input.name,
    ...termsBody(input),
  });
}

export async function addPlanVersion(
  planId: string,
  input: PlanTermsInput,
): Promise<PlanVersion> {
  return apiSend<PlanVersion>(`/api/v1/platform/plans/${planId}/versions`, "POST", termsBody(input));
}

export async function archivePlan(planId: string): Promise<void> {
  await apiSend(`/api/v1/platform/plans/${planId}/archive`, "POST", {});
}

export async function assignPlanToCustomer(
  customerId: string,
  planVersionId: string,
): Promise<void> {
  await apiSend(`/api/v1/platform/customers/${customerId}/subscription`, "POST", {
    plan_version_id: planVersionId,
  });
}
