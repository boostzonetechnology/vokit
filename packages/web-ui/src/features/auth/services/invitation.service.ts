import { apiSend } from "@/api";
import type { AcceptInvitationResult } from "@/features/auth/types/auth.types";

export async function acceptInvitation(input: {
  token: string;
  password: string;
  accept_platform_terms: true;
}): Promise<AcceptInvitationResult> {
  return apiSend<AcceptInvitationResult>("/api/v1/auth/invitations/accept", "POST", input);
}
