export type AuditEvent = {
  id: string;
  actor_id?: string | null;
  actor_role?: string;
  tenant_id?: string | null;
  customer_id?: string | null;
  action?: string;
  entity_type?: string;
  entity_id?: string;
  severity?: string;
  correlation_id?: string;
  ip?: string;
  reason?: string;
  before_summary?: string;
  after_summary?: string;
  payload?: unknown;
  created_at?: string;
};
