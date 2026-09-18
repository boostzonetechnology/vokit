import type { SessionPayload } from "@/api";

export type MfaMethodType = "totp" | "email";

export type MfaChallengeMethod = {
  id: string;
  type: MfaMethodType;
  email_hint?: string | null;
};

export type MfaChallengePayload = {
  mfa_required: true;
  challenge_token: string;
  methods: MfaChallengeMethod[];
  user_id: string;
};

export type LoginResult =
  | { kind: "session"; session: SessionPayload }
  | { kind: "challenge"; challenge: MfaChallengePayload };

export type MfaMethodRecord = {
  id: string;
  type: MfaMethodType;
  status: string;
  email_hint?: string | null;
  verified_at?: string | null;
  created_at?: string | null;
};

export type MfaConfirmResult = {
  method_id: string;
  type: MfaMethodType;
  status: string;
  recovery_codes?: string[];
};

export type TotpEnrollResult = {
  method_id: string;
  otpauth_uri: string;
  secret: string;
};

export type EmailEnrollResult = {
  method_id: string;
  challenge_token: string;
  expires_in: number;
};

export type LoginStep = "credentials" | "challenge" | "privilegedBlock";

export type LoginPortalCopy = {
  title: string;
  subtitle: string;
  heroEyebrow: string;
  heroTitle: string;
};

export type MfaStepUpMode = "totp" | "recovery";

export type AcceptInvitePortalCopy = {
  eyebrow: string;
  heroTitle: string;
  subtitle: string;
};

export type AcceptInvitationResult = {
  user_id: string;
  email: string;
};

export type AcceptInviteFormValues = {
  token: string;
  password: string;
  confirm: string;
  acceptPlatformTerms: boolean;
};
