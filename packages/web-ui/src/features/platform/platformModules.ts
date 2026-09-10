export type PlatformColumn = { key: string; label: string };

export type PlatformModuleConfig = {
  route: string;
  title: string;
  subtitle: string;
  path: string;
  columns: PlatformColumn[];
  empty: string;
  permissionHint?: string;
  apiGaps?: string[];
  /** When API returns a single object instead of a list */
  objectMode?: boolean;
};

/** Platform module catalog aligned to portalNav + SRS Super Admin surfaces. */
export const PLATFORM_MODULES: Record<string, PlatformModuleConfig> = {
  kyc: {
    route: "kyc",
    title: "KYC",
    subtitle: "Agency KYC queue and case status",
    path: "/api/v1/platform/kyc/cases",
    columns: [
      { key: "status", label: "Status" },
      { key: "tenant_id", label: "Agency" },
      { key: "updated_at", label: "Updated" },
      { key: "id", label: "Case" },
    ],
    empty: "No KYC cases.",
    permissionHint: "kyc.review",
  },
  templates: {
    route: "templates",
    title: "Templates",
    subtitle: "Global agent template catalog",
    path: "/api/v1/platform/templates",
    columns: [
      { key: "name", label: "Name" },
      { key: "industry", label: "Industry" },
      { key: "use_case", label: "Use case" },
      { key: "visibility", label: "Visibility" },
      { key: "status", label: "Status" },
      { key: "latest_version", label: "Version" },
    ],
    empty: "No templates yet.",
    permissionHint: "agents.review",
  },
  instructions: {
    route: "instructions",
    title: "Instructions",
    subtitle: "Platform safety / behavior instructions",
    path: "/api/v1/platform/instructions",
    columns: [{ key: "body", label: "Body" }],
    empty: "No platform instructions saved.",
    permissionHint: "agents.review",
    objectMode: true,
  },
  knowledge: {
    route: "knowledge",
    title: "Knowledge",
    subtitle: "Global knowledge sources",
    path: "/api/v1/platform/knowledge",
    columns: [
      { key: "title", label: "Title" },
      { key: "scope", label: "Scope" },
      { key: "id", label: "Id" },
    ],
    empty: "No global knowledge yet.",
    permissionHint: "agents.review",
  },
  numbers: {
    route: "numbers",
    title: "Numbers",
    subtitle: "Phone number inventory and assignments",
    path: "/api/v1/platform/phone-numbers",
    columns: [
      { key: "e164", label: "Number" },
      { key: "status", label: "Status" },
      { key: "country", label: "Country" },
      { key: "assigned_agency_id", label: "Agency" },
      { key: "assigned_agent_id", label: "Agent" },
      { key: "provider", label: "Provider" },
    ],
    empty: "No phone numbers in inventory.",
    permissionHint: "numbers.review",
  },
  transfers: {
    route: "transfers",
    title: "Transfers",
    subtitle: "Transfer destinations across tenants",
    path: "/api/v1/platform/transfers",
    columns: [
      { key: "display_name", label: "Name" },
      { key: "e164", label: "Number" },
      { key: "status", label: "Status" },
      { key: "agency_id", label: "Agency" },
      { key: "customer_id", label: "Customer" },
      { key: "id", label: "Id" },
    ],
    empty: "No transfer destinations.",
    permissionHint: "calls.review",
  },
  plans: {
    route: "plans",
    title: "Plans",
    subtitle: "Subscription plans and versions",
    path: "/api/v1/platform/plans",
    columns: [
      { key: "name", label: "Plan" },
      { key: "status", label: "Status" },
      { key: "id", label: "Id" },
    ],
    empty: "No plans yet.",
    permissionHint: "billing.view",
  },
  invoices: {
    route: "invoices",
    title: "Invoices",
    subtitle: "Customer invoices across agencies",
    path: "/api/v1/platform/invoices",
    columns: [
      { key: "status", label: "Status" },
      { key: "total_minor", label: "Total (minor)" },
      { key: "currency", label: "Currency" },
      { key: "customer_id", label: "Customer" },
      { key: "created_at", label: "Created" },
      { key: "id", label: "Id" },
    ],
    empty: "No invoices yet.",
    permissionHint: "billing.view",
  },
  payments: {
    route: "payments",
    title: "Payments",
    subtitle: "Captured payment settlements",
    path: "/api/v1/platform/payments",
    columns: [
      { key: "status", label: "Status" },
      { key: "amount_minor", label: "Amount (minor)" },
      { key: "currency", label: "Currency" },
      { key: "invoice_id", label: "Invoice" },
      { key: "created_at", label: "Created" },
      { key: "id", label: "Id" },
    ],
    empty: "No payments yet.",
    permissionHint: "billing.view",
  },
  disputes: {
    route: "disputes",
    title: "Disputes",
    subtitle: "Chargebacks and payment disputes",
    path: "/api/v1/platform/disputes",
    columns: [
      { key: "status", label: "Status" },
      { key: "invoice_id", label: "Invoice" },
      { key: "amount_minor", label: "Amount (minor)" },
      { key: "created_at", label: "Created" },
      { key: "id", label: "Id" },
    ],
    empty: "No disputes yet.",
    permissionHint: "billing.view",
  },
  payouts: {
    route: "payouts",
    title: "Payouts",
    subtitle: "Agency payout queue and history",
    path: "/api/v1/platform/payouts",
    columns: [
      { key: "status", label: "Status" },
      { key: "amount_minor", label: "Amount (minor)" },
      { key: "tenant_id", label: "Agency" },
      { key: "created_at", label: "Created" },
      { key: "id", label: "Id" },
    ],
    empty: "No payouts yet.",
    permissionHint: "payouts.review",
  },
  calls: {
    route: "calls",
    title: "Calls",
    subtitle: "Call index across tenants",
    path: "/api/v1/platform/calls",
    columns: [
      { key: "status", label: "Status" },
      { key: "direction", label: "Direction" },
      { key: "agent_id", label: "Agent" },
      { key: "billed_minutes", label: "Minutes" },
      { key: "started_at", label: "Started" },
      { key: "id", label: "Id" },
    ],
    empty: "No calls yet.",
    permissionHint: "calls.review",
  },
  integrations: {
    route: "integrations",
    title: "Integrations",
    subtitle: "Integration connections across tenants",
    path: "/api/v1/platform/integrations",
    columns: [
      { key: "provider", label: "Provider" },
      { key: "status", label: "Status" },
      { key: "agency_id", label: "Agency" },
      { key: "customer_id", label: "Customer" },
      { key: "id", label: "Id" },
    ],
    empty: "No integrations yet.",
    permissionHint: "integrations.review",
  },
  risk: {
    route: "risk",
    title: "Risk",
    subtitle: "Payment risk and chargeback cases",
    path: "/api/v1/platform/risk/cases",
    columns: [
      { key: "status", label: "Status" },
      { key: "customer_id", label: "Customer" },
      { key: "tenant_id", label: "Agency" },
      { key: "updated_at", label: "Updated" },
      { key: "id", label: "Case" },
    ],
    empty: "No risk cases.",
    permissionHint: "risk.review",
  },
  notifications: {
    route: "notifications",
    title: "Notifications",
    subtitle: "Your platform inbox",
    path: "/api/v1/platform/notifications",
    columns: [
      { key: "title", label: "Title" },
      { key: "category", label: "Category" },
      { key: "read_at", label: "Read" },
      { key: "created_at", label: "Created" },
      { key: "id", label: "Id" },
    ],
    empty: "No notifications.",
  },
  "notice-templates": {
    route: "notice-templates",
    title: "Notice templates",
    subtitle: "Notification templates for platform events",
    path: "/api/v1/platform/notification-templates",
    columns: [
      { key: "name", label: "Name" },
      { key: "event", label: "Event" },
      { key: "channel", label: "Channel" },
      { key: "id", label: "Id" },
    ],
    empty: "No notice templates yet.",
  },
  audit: {
    route: "audit",
    title: "Audit",
    subtitle: "Immutable audit event search",
    path: "/api/v1/platform/audit-events",
    columns: [
      { key: "event", label: "Event" },
      { key: "actor_id", label: "Actor" },
      { key: "created_at", label: "When" },
      { key: "id", label: "Id" },
    ],
    empty: "No audit events.",
    permissionHint: "audit.view",
  },
  users: {
    route: "users",
    title: "Users",
    subtitle: "Platform staff users",
    path: "/api/v1/platform/users",
    columns: [
      { key: "email", label: "Email" },
      { key: "status", label: "Status" },
      { key: "role", label: "Role" },
      { key: "id", label: "Id" },
    ],
    empty: "No platform users listed.",
    permissionHint: "users.manage",
  },
  settings: {
    route: "settings",
    title: "Settings",
    subtitle: "Platform configuration (secrets masked)",
    path: "/api/v1/platform/settings",
    columns: [
      { key: "support_email", label: "Support email" },
      { key: "payout_hold_days", label: "Hold days" },
      { key: "id", label: "Id" },
    ],
    empty: "Settings payload empty.",
    permissionHint: "settings.manage",
    objectMode: true,
  },
};

export function cellValue(value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

