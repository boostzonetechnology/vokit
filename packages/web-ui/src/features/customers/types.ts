export type CustomerSubscription = {
  id?: string;
  plan_id?: string;
  plan_version_id?: string;
  plan_name?: string;
  plan_version?: number;
  status?: string;
  included_minutes?: number;
};

export type MinuteLot = {
  id: string;
  kind?: string;
  granted_minutes?: number;
  remaining_minutes?: number;
};

export type CustomerUsage = {
  remaining_minutes?: number;
  lots?: MinuteLot[];
};

export type CustomerRecord = {
  id: string;
  agency_id?: string;
  display_name?: string;
  status?: string;
  legal_name?: string;
  owner_email?: string;
  phone?: string;
  country?: string;
  timezone?: string;
  created_at?: string | null;
  updated_at?: string | null;
  remaining_minutes?: number;
  subscription?: CustomerSubscription | null;
};

export type CreateCustomerInput = {
  agency_id: string;
  display_name: string;
  owner_email: string;
  legal_name?: string;
  phone?: string;
  country?: string;
  timezone?: string;
};

/** Agency create: tenant comes from session — no agency_id in body. */
export type AgencyCreateCustomerInput = {
  display_name: string;
  owner_email: string;
  legal_name?: string;
  phone?: string;
  country?: string;
  timezone?: string;
};

export type CustomerResourceBundle = {
  agents: Array<{ id: string; display_name?: string; status?: string }>;
  numbers: Array<{ id: string; e164?: string; status?: string }>;
  calls: Array<{ id: string; status?: string; billed_minutes?: number; started_at?: string | null }>;
  knowledge: Array<{ id: string; title?: string; name?: string; status?: string }>;
  integrations: Array<{ id: string; provider?: string; status?: string }>;
  invoices: Array<{ id: string; status?: string; total_minor?: number; currency?: string }>;
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
  { action: "activate", label: "Activate / reactivate", needsReason: false },
  { action: "suspend", label: "Suspend", needsReason: true },
  { action: "close", label: "Close", needsReason: true },
] as const;

export const CUSTOMER_STATUSES = ["invited", "active", "suspended", "closed"] as const;
