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
  content_type?: string;
  agency_visible?: boolean;
  agency_visible_at?: string | null;
};

export type LedgerEntry = {
  id: string;
  kind?: string;
  amount_minor?: number;
  currency?: string;
  invoice_id?: string | null;
  payment_id?: string | null;
  reason?: string;
  earned_at?: string | null;
  available_at?: string | null;
  state?: string;
  eligible_base_minor?: number;
  rate_bps_snapshot?: number;
};

export type PayoutReceipt = {
  receipt_number?: string;
  payout_id?: string;
  agency_id?: string;
  agency_display_name?: string;
  agency_legal_name?: string;
  amount_minor?: number;
  currency?: string;
  method_label?: string;
  transaction_ref?: string;
  status?: string;
  requested_at?: string | null;
  paid_at?: string | null;
  issuer?: string;
  disclaimer?: string;
};

export type PayoutMethodRecord = {
  id: string;
  beneficiary_name?: string;
  account_identifier_masked?: string;
  bank_name?: string;
  country?: string;
  currency?: string;
  label?: string;
  status?: string;
  is_default?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export type PayoutMethodInput = {
  beneficiary_name: string;
  account_identifier: string;
  bank_name: string;
  country: string;
  currency?: string;
  is_default?: boolean;
};
