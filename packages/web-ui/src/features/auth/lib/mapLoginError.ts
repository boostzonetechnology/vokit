import { isApiError } from "@/api";

export function mapLoginError(cause: unknown): { message: string; privilegedBlock: boolean } {
  if (!isApiError(cause)) {
    return { message: "Sign-in failed.", privilegedBlock: false };
  }
  if (cause.status === 403 && cause.code === "mfa_required") {
    return {
      message:
        "This privileged role requires MFA enrollment before you can sign in. Ask a Super Admin to reset MFA or temporarily disable the privileged MFA requirement so you can enroll.",
      privilegedBlock: true,
    };
  }
  if (cause.code === "rate_limited") {
    return {
      message: cause.message || "Too many attempts. Wait a few minutes and try again.",
      privilegedBlock: false,
    };
  }
  return {
    message: cause.message || "Sign-in failed.",
    privilegedBlock: false,
  };
}
