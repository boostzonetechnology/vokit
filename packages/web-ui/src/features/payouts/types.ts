export type WalletBuckets = {
  pending_minor?: number;
  on_hold_minor?: number;
  available_minor?: number;
  frozen_minor?: number;
  withdrawal_pending_minor?: number;
  lifetime_paid_minor?: number;
  currency?: string;
};

export type PayoutRecord = {
  id: string;
  agency_id?: string;
  amount_minor?: number;
  currency?: string;
  status?: string;
  method_label?: string;
  transaction_ref?: string;
  receipt_number?: string | null;
  paid_at?: string | null;
  requested_at?: string | null;
};

export type AgencyOption = {
  id: string;
  display_name?: string;
};

export type PayoutProof = {
  payout_id?: string;
  object_ref?: string;
  content_type?: string;
  checksum?: string;
};

export const PAYOUT_ACTIONS = [
  { value: "approve", label: "Approve" },
  { value: "reject", label: "Reject" },
  { value: "freeze", label: "Freeze" },
  { value: "process", label: "Process" },
] as const;
