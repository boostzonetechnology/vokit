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

/** Full agent payload from GET/PATCH /platform/agents/{id}. */
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
