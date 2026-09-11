export type TransferDestination = {
  id: string;
  agency_id?: string;
  customer_id?: string;
  kind?: string;
  label?: string;
  status?: string;
  platform_disabled?: boolean;
  target?: string;
};

export type CallIndexRow = {
  id: string;
  agency_id?: string;
  customer_id?: string;
  agent_id?: string;
  e164?: string;
  remote_e164?: string;
  direction?: string;
  status?: string;
  end_reason?: string;
  billed_minutes?: number;
  started_at?: string | null;
};
