export type PlatformAgentRow = {
  id: string;
  agency_id?: string;
  customer_id?: string;
  display_name?: string;
  status?: string;
  agent_type?: string;
  published_version?: number | null;
  production_routable?: boolean;
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
