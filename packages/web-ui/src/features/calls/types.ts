export type CallRecord = {
  id: string;
  agency_id?: string;
  customer_id?: string;
  agent_id?: string;
  e164?: string;
  remote_e164?: string;
  edge_call_id?: string;
  direction?: string;
  status?: string;
  voicemail_status?: string;
  billed_minutes?: number;
  started_at?: string | null;
  duration_seconds?: number;
  end_reason?: string;
};

export type CallArtifact = {
  id?: string;
  kind?: string;
  status?: string;
  hold?: boolean;
  created_at?: string;
};
