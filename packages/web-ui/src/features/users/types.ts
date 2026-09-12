/** Fixed platform roles from control_plane identity catalog (not API-editable). */
export const PLATFORM_ROLES = [
  "super_admin",
  "finance_admin",
  "compliance_kyc",
  "support_admin",
] as const;

export const SENSITIVE_PERMISSIONS = [
  { key: "kyc.review", label: "KYC review" },
  { key: "payout.approve", label: "Payout approve" },
  { key: "wallet.adjust", label: "Wallet adjustment" },
  { key: "commission.edit", label: "Commission edit" },
  { key: "impersonation.use", label: "Impersonation" },
] as const;

/** Mirrors apps/api/control_plane/identity/domain/roles.py ROLE_PERMISSIONS (platform). */
export const PLATFORM_ROLE_PERMISSIONS: Record<string, string[]> = {
  super_admin: [
    "users.invite",
    "users.disable",
    "tenants.view",
    "tenants.provision",
    "tenants.migrate",
    "tenants.route",
    "agencies.view",
    "agencies.create",
    "agencies.manage",
    "customers.view",
    "customers.create",
    "plans.manage",
    "billing.view",
    "kyc.review",
    "risk.review",
    "agents.review",
    "numbers.review",
    "calls.review",
    "transfers.review",
    "recordings.review",
    "integrations.review",
    "audit.view",
    "settings.manage",
    "notifications.manage",
    "payout.approve",
    "wallet.adjust",
    "commission.edit",
    "impersonation.use",
  ],
  finance_admin: ["payout.approve", "wallet.adjust", "billing.view"],
  compliance_kyc: ["kyc.review", "risk.review", "recordings.review"],
  support_admin: [],
};

export type PlatformUser = {
  id: string;
  membership_id?: string;
  email?: string;
  principal_type?: string;
  role?: string;
  tenant_id?: string | null;
  customer_id?: string | null;
  status?: string;
};

export type PlatformInvitation = {
  id: string;
  email?: string;
  principal_type?: string;
  role?: string;
  tenant_id?: string | null;
  customer_id?: string | null;
  status?: string;
  token?: string;
};
