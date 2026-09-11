export type CustomerRecord = {
  id: string;
  agency_id?: string;
  display_name?: string;
  status?: string;
  owner_invitation_token?: string;
};

export type PlanVersionOption = {
  id: string;
  plan_id?: string;
  plan_name?: string;
  version?: number;
  price_minor?: number;
  included_minutes?: number;
  currency?: string;
};

export type AgencyOption = {
  id: string;
  display_name?: string;
};

export const CUSTOMER_STATUS_ACTIONS = [
  { action: "suspend", label: "Suspend" },
  { action: "activate", label: "Activate / reactivate" },
  { action: "close", label: "Close" },
] as const;
