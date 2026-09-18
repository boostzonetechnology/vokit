import type { AcceptInviteFormValues } from "@/features/auth/types/auth.types";

const MIN_PASSWORD_LENGTH = 12;

/** Client-side accept-invite checks before the API call. */
export function validateAcceptInviteForm(values: AcceptInviteFormValues): string | null {
  if (!values.token) {
    return "Invitation link is missing a token. Open the button from your email again.";
  }
  if (values.password.length < MIN_PASSWORD_LENGTH) {
    return "Password must be at least 12 characters.";
  }
  if (values.password !== values.confirm) {
    return "Passwords do not match.";
  }
  if (!values.acceptPlatformTerms) {
    return "You must accept the platform terms to continue.";
  }
  return null;
}
