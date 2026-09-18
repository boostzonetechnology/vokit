import type { MfaChallengeMethod, MfaMethodRecord } from "@/features/auth/types/auth.types";

export function mfaMethodTitle(type: MfaChallengeMethod["type"] | MfaMethodRecord["type"]): string {
  return type === "totp" ? "Authenticator app" : "Email OTP";
}

export function mfaChallengeMethodLabel(method: MfaChallengeMethod): string {
  if (method.type === "totp") {
    return "Authenticator app";
  }
  return `Email${method.email_hint ? ` (${method.email_hint})` : ""}`;
}

export function mfaChallengeMethodHint(method: MfaChallengeMethod | undefined): string {
  if (!method) {
    return "";
  }
  if (method.type === "totp") {
    return "Use your authenticator app.";
  }
  return `Email code${method.email_hint ? ` to ${method.email_hint}` : ""}.`;
}

export function isActiveMfaMethod(method: MfaMethodRecord): boolean {
  return (method.status || "").toLowerCase() === "active";
}
