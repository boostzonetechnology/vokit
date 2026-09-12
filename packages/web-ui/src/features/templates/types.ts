export type TemplateRecord = {
  id: string;
  name?: string;
  industry?: string;
  use_case?: string;
  description?: string;
  languages?: string;
  visibility?: string;
  status?: string;
  latest_version?: number | null;
};

export type AgencyOption = {
  id: string;
  display_name?: string;
};

/** Mirrors backend ALLOWED_TOOLS */
export const TEMPLATE_TOOLS = [
  "create_lead",
  "create_contact",
  "update_contact",
  "book_appointment",
  "lookup_customer",
  "create_ticket",
  "send_notification",
  "check_order",
  "create_invoice_context",
  "transfer_call",
  "invoke_webhook",
] as const;

export const AGENT_TYPES = [
  "receptionist",
  "appointment",
  "support",
  "sales",
  "real_estate",
  "medical_receptionist",
  "restaurant",
  "hotel",
  "ecommerce",
  "dispatch",
  "after_hours",
  "faq",
  "custom",
] as const;

export const VISIBILITY_OPTIONS = [
  { value: "global", label: "Global" },
  { value: "selected", label: "Selected agencies" },
  { value: "internal", label: "Internal only" },
] as const;
