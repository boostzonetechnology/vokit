export type AgencyCapabilities = {
  create_customers: boolean;
  create_agents: boolean;
  purchase_numbers: boolean;
  request_payouts: boolean;
  existing_customer_services: boolean;
};

export type AgencyRecord = {
  id: string;
  display_name?: string;
  legal_name?: string;
  tenant_status?: string;
  status?: string;
  currency?: string;
  commission_rate_bps?: number;
  rate_effective_at?: string | null;
  capabilities?: AgencyCapabilities;
  owner_invitation_token?: string;
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

export type AgencyDashboardSlice = {
  currency?: string;
  kpis?: Array<{ key: string; value: string | number | boolean; label?: string }>;
  financial?: Record<string, string | number>;
};

export const CAPABILITY_FIELDS: Array<{ key: keyof AgencyCapabilities; label: string }> = [
  { key: "create_customers", label: "Customer creation" },
  { key: "create_agents", label: "Agent creation" },
  { key: "purchase_numbers", label: "Number purchase" },
  { key: "request_payouts", label: "Payout requests" },
  { key: "existing_customer_services", label: "Existing customer services" },
];

export const STATUS_ACTIONS = [
  { action: "activate", label: "Activate / reactivate" },
  { action: "restrict", label: "Restrict" },
  { action: "review", label: "Under review" },
  { action: "suspend", label: "Suspend" },
  { action: "close", label: "Close" },
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
