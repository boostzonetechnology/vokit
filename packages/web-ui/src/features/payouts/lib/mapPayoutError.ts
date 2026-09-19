import { isApiError } from "@/api";

export function mapPayoutError(cause: unknown, fallback: string): string {
  if (!isApiError(cause)) return fallback;
  const copy: Record<string, string> = {
    payout_method_unusable: "Selected payout method is not available for withdrawal.",
    payout_kyc_unverified: "Payout blocked until agency KYC is verified.",
    payout_kyc_frozen: "Wallet is frozen. Payouts are blocked until risk review clears.",
    payout_agency_blocked: "Agency status or capabilities do not allow payouts.",
    kyc_not_verified: "Payout blocked until agency KYC is verified.",
    kyc_frozen: "Wallet is frozen. Payouts are blocked until risk review clears.",
    payout_not_allowed: "Agency status or capabilities do not allow payouts.",
    insufficient_available: "Amount exceeds available wallet balance.",
    payout_insufficient: "Amount exceeds available wallet balance.",
    validation_error: cause.message || "Check amount and payout method.",
    idempotency_conflict: "This payout request was already submitted.",
    not_found: "Payout or method not found.",
  };
  if (cause.code && copy[cause.code]) return copy[cause.code];
  return cause.message || fallback;
}
