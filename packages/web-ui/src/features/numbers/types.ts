export type PhoneNumberRecord = {
  id: string;
  e164?: string;
  country?: string;
  area?: string;
  capabilities?: string[];
  provider?: string;
  status?: string;
  monthly_cost_minor?: number;
  currency?: string;
  assigned_agency_id?: string | null;
  assigned_customer_id?: string | null;
  assigned_agent_id?: string | null;
  reserved_until?: string | null;
};

export type ReconcileResult = {
  expired_reservations?: number;
  provider_orphans?: string[];
  local_orphans?: string[];
};
