export type PlanVersion = {
  id: string;
  plan_id?: string;
  version?: number;
  price_minor?: number;
  currency?: string;
  included_minutes?: number;
  allow_topups?: boolean;
  topup_minutes?: number;
  topup_price_minor?: number;
  overage_enabled?: boolean;
  overage_price_per_minute_minor?: number;
  grace_seconds?: number;
  max_agents?: number;
  max_phone_numbers?: number;
  max_concurrency?: number;
  recording_allowed?: boolean;
  allowed_integrations?: string[];
  used?: boolean;
};

export type PlanRecord = {
  id: string;
  name?: string;
  status?: string;
  versions?: PlanVersion[];
  available_integrations?: string[];
};

export type CustomerOption = {
  id: string;
  display_name?: string;
  agency_id?: string;
};

/** Shared create-plan / add-version body (ADR-011 entitlements included). */
export type PlanTermsInput = {
  name?: string;
  price_minor: number;
  included_minutes: number;
  allow_topups: boolean;
  topup_minutes: number;
  topup_price_minor: number;
  overage_enabled: boolean;
  overage_price_per_minute_minor: number;
  grace_seconds: number;
  max_agents: number;
  max_phone_numbers: number;
  max_concurrency: number;
  recording_allowed: boolean;
  allowed_integrations: string[];
};

export function formatCapLimit(value?: number): string {
  if (typeof value !== "number") return "—";
  return value === 0 ? "Unlimited" : String(value);
}
