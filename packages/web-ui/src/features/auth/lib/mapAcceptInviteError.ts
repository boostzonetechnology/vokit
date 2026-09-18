import { isApiError } from "@/api";

export function mapAcceptInviteError(cause: unknown): string {
  if (isApiError(cause)) {
    return cause.message || "Could not accept invitation.";
  }
  return "Could not accept invitation.";
}
