export type AgencyCapabilities = {
  create_customers: boolean;
  create_agents: boolean;
  purchase_numbers: boolean;
  request_payouts: boolean;
  existing_customer_services: boolean;
};

export type AgencyDatabase = {
  host?: string;
  port?: number;
  name?: string;
  username?: string;
  status?: string;
  schema_version?: string;
  tls_required?: boolean;
};

export type AgencyRecord = {
  id: string;
  display_name?: string;
  legal_name?: string;
  tenant_status?: string;
  status?: string;
  currency?: string;
  commission_rate_bps?: number;
  previous_commission_rate_bps?: number;
  rate_effective_at?: string | null;
  capabilities?: AgencyCapabilities;
  database?: AgencyDatabase;
};

export type CreateAgencyInput = {
  display_name: string;
  legal_name: string;
  owner_email: string;
  commission_rate_bps: number;
  currency: string;
  capabilities: AgencyCapabilities;
  database: {
    username: string;
    password: string;
    host?: string;
    port?: number;
  };
};

export type AgencyNote = {
  id: string;
  agency_id?: string;
  body: string;
  risk_flag?: boolean;
  created_by_id?: string;
  created_at?: string | null;
};

export type WalletBuckets = {
  pending_minor?: number;
  on_hold_minor?: number;
  available_minor?: number;
  frozen_minor?: number;
  withdrawal_pending_minor?: number;
  lifetime_paid_minor?: number;
  currency?: string;
};

export type AgencyPayoutRow = {
  id?: string;
  status?: string;
  amount_minor?: number;
  currency?: string;
  paid_at?: string | null;
  method_label?: string;
};

export type AgencyFinance = {
  agency_id: string;
  mrr_minor: number;
  commission_mrr_minor: number;
  customer_revenue_minor: number;
  commission_earned_minor: number;
  buckets: WalletBuckets;
  payouts: AgencyPayoutRow[];
};

export type SetCommissionInput = {
  commission_rate_bps: number;
  reason: string;
  rate_effective_at?: string;
};

export type SetStatusInput = {
  action: string;
  confirm: true;
  reason?: string;
};

export type SetCapabilitiesInput = {
  confirm: true;
  reason: string;
  capabilities: AgencyCapabilities;
};

export type AgencyDetailTab =
  | "overview"
  | "profile"
  | "commission"
  | "status"
  | "capabilities"
  | "financial"
  | "resources"
  | "notes";

export const CAPABILITY_FIELDS: Array<{ key: keyof AgencyCapabilities; label: string }> = [
  { key: "create_customers", label: "Customer creation" },
  { key: "create_agents", label: "Agent creation" },
  { key: "purchase_numbers", label: "Number purchase" },
  { key: "request_payouts", label: "Payout requests" },
  { key: "existing_customer_services", label: "Existing customer services" },
];

export const STATUS_ACTIONS = [
  { action: "activate", label: "Activate / reactivate", needsReason: false },
  { action: "restrict", label: "Restrict", needsReason: true },
  { action: "review", label: "Under review", needsReason: true },
  { action: "suspend", label: "Suspend", needsReason: true },
  { action: "close", label: "Close", needsReason: true },
] as const;

export const AGENCY_STATUS_FILTERS = [
  "invited",
  "pending",
  "active",
  "restricted",
  "under_review",
  "suspended",
  "closed",
] as const;

export function defaultCapabilities(): AgencyCapabilities {
  return {
    create_customers: true,
    create_agents: true,
    purchase_numbers: true,
    request_payouts: true,
    existing_customer_services: true,
  };
}

export function statusActionNeedsReason(action: string): boolean {
  return STATUS_ACTIONS.some((item) => item.action === action && item.needsReason);
}
