export type KycCase = {
  id: string;
  agency_id?: string;
  status?: string;
  reason_code?: string;
  external_note?: string;
  internal_note?: string;
  frozen?: boolean;
  session_id?: string;
  inquiry_id?: string;
  last_event_id?: string;
};

export type KycSettings = {
  provider_slug?: string;
  api_key_ref?: string;
  webhook_secret_ref?: string;
  hosted_base_url?: string;
};

export type AgencyOption = {
  id: string;
  display_name?: string;
};

export const KYC_STATUSES = [
  "not_started",
  "incomplete",
  "submitted",
  "under_review",
  "more_information_required",
  "verified",
  "rejected",
  "expired",
  "suspended",
] as const;

export const DECISION_STATUSES = [
  { value: "verified", label: "Verify" },
  { value: "rejected", label: "Reject" },
  { value: "more_information_required", label: "Request more information" },
] as const;
