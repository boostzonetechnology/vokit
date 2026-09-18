import { isApiError } from "@/api";

export function mapMfaError(cause: unknown, fallback: string): string {
  if (!isApiError(cause)) {
    return fallback;
  }
  if (cause.code === "mfa_last_method") {
    return (
      cause.message ||
      "You cannot disable your last MFA method while privileged MFA is required."
    );
  }
  if (cause.code === "mfa_challenge_locked") {
    return (
      cause.message ||
      "This challenge is locked after too many failed attempts. Sign in again."
    );
  }
  if (cause.code === "mfa_invalid_code") {
    return cause.message || "Invalid verification code.";
  }
  if (cause.code === "rate_limited") {
    return cause.message || "Too many attempts. Wait a few minutes and try again.";
  }
  return cause.message || fallback;
}
