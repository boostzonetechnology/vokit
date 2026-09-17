export type PlatformAgentRow = {
  id: string;
  agency_id?: string;
  customer_id?: string;
  display_name?: string;
  status?: string;
  agent_type?: string;
  published_version?: number | null;
  production_routable?: boolean;
  status_locked?: boolean;
  status_actor?: string | null;
  assigned_e164?: string | null;
};

/** One business-hours window as returned/accepted by agent PATCH. weekday: Mon=0 … Sun=6. */
export type BusinessHoursWindow = {
  weekday: number;
  start: string;
  end: string;
};

/** Full agent payload from GET/PATCH /platform|agency/agents/{id}. */
export type PlatformAgentDetail = PlatformAgentRow & {
  timezone?: string;
  voice_provider?: string;
  voice_id?: string;
  language?: string;
  greeting?: string;
  fallback_behavior?: string;
  inbound_enabled?: boolean;
  outbound_enabled?: boolean;
  recording_disclosure?: boolean;
  instructions?: string;
  template_instructions?: string;
  tools?: string[];
  draft_version?: number | null;
  template_id?: string | null;
  customer_can_edit?: boolean;
  business_hours?: BusinessHoursWindow[];
  voicemail_greeting?: string;
  outbound_voicemail_message?: string;
  default_transfer_id?: string | null;
  speaking_style?: string;
  speaking_speed?: number | null;
  role?: string;
  goals?: string;
  constraints?: string;
  silence_timeout_seconds?: number | null;
  max_call_duration_seconds?: number | null;
  tool_schema_overrides?: Record<string, unknown>;
  tool_schemas?: Record<string, unknown>;
};

export type AgencyAgentDetail = PlatformAgentDetail;

export type AgentRoutingResult = {
  routable?: boolean;
  reason?: string | null;
};

export type AgentKnowledgeAttachment = {
  source_id: string;
  scope?: string;
  group_id?: string;
  title?: string;
  status?: string;
};

export type PlatformAgentDiagnostics = {
  runtime?: {
    resolved_instructions?: string;
    production_routable?: boolean;
    reason?: string;
  };
  recent_calls?: Array<{
    id: string;
    status?: string;
    direction?: string;
    billed_minutes?: number;
    e164?: string;
    remote_e164?: string;
  }>;
  errors?: Array<{
    id: string;
    kind?: string;
    status?: string;
    message?: string;
  }>;
  integrations?: Array<{
    id: string;
    provider?: string;
    status?: string;
  }>;
};

export type AgencyOption = { id: string; display_name?: string };
export type CustomerOption = {
  id: string;
  display_name?: string;
  agency_id?: string;
};
export type PhoneNumberRow = {
  id: string;
  e164?: string;
  assigned_agent_id?: string | null;
};
export type CallRow = {
  id: string;
  agent_id?: string;
  status?: string;
  direction?: string;
  billed_minutes?: number;
  started_at?: string | null;
  ended_at?: string | null;
  remote_e164?: string;
};
export type IntegrationRow = {
  id: string;
  provider?: string;
  status?: string;
  customer_id?: string;
  agency_id?: string;
};

/** Mirror of BE ALLOWED_TOOLS — AgentAction allowlist. */
export const ALLOWED_AGENT_TOOLS = [
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

export const WEEKDAY_LABELS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
] as const;

export const FALLBACK_BEHAVIORS = ["message", "transfer", "hangup"] as const;

export const SILENCE_TIMEOUT_RANGE = { min: 5, max: 120, default: 20 } as const;
export const MAX_CALL_DURATION_RANGE = { min: 60, max: 7200, default: 1800 } as const;
export const SPEAKING_SPEED_RANGE = { min: 0.5, max: 2, default: 1 } as const;
