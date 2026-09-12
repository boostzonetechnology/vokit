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
  used?: boolean;
};

export type PlanRecord = {
  id: string;
  name?: string;
  status?: string;
  versions?: PlanVersion[];
};

export type CustomerOption = {
  id: string;
  display_name?: string;
  agency_id?: string;
};

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
};
