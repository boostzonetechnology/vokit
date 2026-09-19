export type CustomerSubscription = {
  id?: string;
  plan_id?: string;
  plan_version_id?: string;
  plan_name?: string;
  plan_version?: number;
  status?: string;
  included_minutes?: number;
  period_started_at?: string | null;
  period_end?: string | null;
  pending_kind?: string | null;
  pending_plan_version_id?: string | null;
  pending_invoice_id?: string | null;
  pending_effective_at?: string | null;
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
  plan_id?: string | null;
  plan_name?: string | null;
  plan_version?: number | null;
  subscription_status?: string | null;
  payment_due?: boolean;
  subscription?: CustomerSubscription | null;
};

export type PlanOption = {
  id: string;
  name?: string;
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

export type SubscriptionChangeResult = {
  kind?: string;
  invoice?: {
    id?: string;
    status?: string;
    total_minor?: number;
    currency?: string;
    due_at?: string | null;
  };
  subscription?: CustomerSubscription | null;
};

export const CUSTOMER_STATUS_ACTIONS = [
  { action: "activate", label: "Activate / reactivate", needsReason: false },
  { action: "suspend", label: "Suspend", needsReason: true },
  { action: "close", label: "Close", needsReason: true },
] as const;

export const CUSTOMER_STATUSES = ["invited", "active", "suspended", "closed"] as const;

export function mapCustomerError(cause: unknown, fallback: string): string {
  if (
    cause &&
    typeof cause === "object" &&
    "message" in cause &&
    typeof (cause as { message: unknown }).message === "string"
  ) {
    const code =
      "code" in cause && typeof (cause as { code: unknown }).code === "string"
        ? (cause as { code: string }).code
        : "";
    const message = (cause as { message: string }).message;
    const copy: Record<string, string> = {
      subscription_exists: "This customer already has a subscription. Use plan change instead.",
      subscription_required: "Assign a plan before changing it.",
      subscription_change_pending: "A plan change is already pending. Finish or wait for it.",
      extras_exceed_plan:
        "Downgrade blocked: active agents or numbers exceed the target plan caps.",
      same_plan_version: "Customer is already on this plan version.",
      owner_conflict: "That owner email already has a conflicting membership.",
      agency_cannot_create_customer: "Customer creation is blocked by agency status or capability.",
    };
    return copy[code] || message || fallback;
  }
  return fallback;
}
