import { isApiError } from "@/api";

const AGENCY_ERROR_COPY: Record<string, string> = {
  confirmation_required: "Confirm the checkbox before applying this change.",
  validation_error: "Check required fields (reason, confirm, or date) and try again.",
  agency_closed: "This agency is closed. Status and most commercial changes are blocked.",
  invalid_agency_status: "That status transition is not allowed from the current status.",
  agency_cannot_create_customer: "Customer creation is blocked by agency status or capability.",
  agency_cannot_create_agent: "Agent creation is blocked by agency status or capability.",
  number_purchase_blocked: "Number purchase is blocked by agency status or capability.",
  payout_agency_blocked:
    "Payout requests are blocked (agency status, KYC, freeze, or request_payouts off).",
  customer_services_disabled:
    "Existing customer services are off — new production calls are blocked.",
  customer_risk_blocked: "Customer risk status blocks this commercial action.",
  not_found: "Agency not found.",
};

export function mapAgencyError(cause: unknown, fallback: string): string {
  if (!isApiError(cause)) {
    return fallback;
  }
  return AGENCY_ERROR_COPY[cause.code] || cause.message || fallback;
}
