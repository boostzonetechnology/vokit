import { apiGet, apiSend, type SessionPayload } from "@/api";
import type {
  EmailEnrollResult,
  MfaConfirmResult,
  MfaMethodRecord,
  TotpEnrollResult,
} from "@/features/auth/types/auth.types";

export async function listMfaMethods(): Promise<MfaMethodRecord[]> {
  const data = await apiGet<{ methods: MfaMethodRecord[] }>("/api/v1/auth/mfa/methods");
  return data.methods ?? [];
}

export async function enrollTotp(): Promise<TotpEnrollResult> {
  return apiSend<TotpEnrollResult>("/api/v1/auth/mfa/totp/enroll", "POST", {});
}

export async function confirmTotp(input: {
  method_id: string;
  code: string;
}): Promise<MfaConfirmResult> {
  return apiSend<MfaConfirmResult>("/api/v1/auth/mfa/totp/confirm", "POST", input);
}

export async function enrollEmail(): Promise<EmailEnrollResult> {
  return apiSend<EmailEnrollResult>("/api/v1/auth/mfa/email/enroll", "POST", {});
}

export async function confirmEmail(input: {
  method_id: string;
  challenge_token: string;
  code: string;
}): Promise<MfaConfirmResult> {
  return apiSend<MfaConfirmResult>("/api/v1/auth/mfa/email/confirm", "POST", input);
}

export async function disableMfaMethod(
  methodId: string,
  input: {
    code?: string;
    verify_method_id?: string;
    recovery_code?: string;
  },
): Promise<{ disabled: boolean; method_id: string }> {
  return apiSend(`/api/v1/auth/mfa/methods/${methodId}/disable`, "POST", input);
}

export async function regenerateRecoveryCodes(input: {
  code?: string;
  method_id?: string;
  recovery_code?: string;
}): Promise<string[]> {
  const data = await apiSend<{ recovery_codes: string[] }>(
    "/api/v1/auth/mfa/recovery/regenerate",
    "POST",
    input,
  );
  return data.recovery_codes ?? [];
}

export async function sendMfaChallenge(input: {
  challenge_token: string;
  method_id: string;
}): Promise<{ sent: boolean; expires_in?: number }> {
  return apiSend("/api/v1/auth/mfa/challenge/send", "POST", input);
}

export async function verifyMfaChallenge(input: {
  challenge_token: string;
  method_id?: string;
  code?: string;
  recovery_code?: string;
}): Promise<SessionPayload> {
  return apiSend<SessionPayload>("/api/v1/auth/mfa/challenge/verify", "POST", input);
}

export async function resetUserMfa(
  userId: string,
  reason: string,
): Promise<{ reset: boolean; methods_disabled?: number }> {
  return apiSend(`/api/v1/platform/users/${userId}/mfa/reset`, "POST", { reason });
}
