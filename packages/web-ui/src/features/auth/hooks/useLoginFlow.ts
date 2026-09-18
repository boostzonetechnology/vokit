import { FormEvent, useState } from "react";

import { isApiError, login, type SessionPayload } from "@/api";
import { mapLoginError } from "@/features/auth/lib/mapLoginError";
import { mapMfaError } from "@/features/auth/lib/mapMfaError";
import { verifyMfaChallenge } from "@/features/auth/services/mfa.service";
import type {
  LoginStep,
  MfaChallengePayload,
} from "@/features/auth/types/auth.types";

export function useLoginFlow(options: {
  onSession: (session: SessionPayload) => Promise<void>;
}) {
  const [step, setStep] = useState<LoginStep>("credentials");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [challenge, setChallenge] = useState<MfaChallengePayload | null>(null);

  function resetToCredentials() {
    setStep("credentials");
    setChallenge(null);
    setError("");
    setPassword("");
  }

  async function onCredentialsSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await login(email, password);
      if (result.kind === "challenge") {
        setChallenge(result.challenge);
        setStep("challenge");
        setPassword("");
        return;
      }
      setChallenge(null);
      setStep("credentials");
      await options.onSession(result.session);
    } catch (cause) {
      const mapped = mapLoginError(cause);
      setError(mapped.message);
      if (mapped.privilegedBlock) {
        setStep("privilegedBlock");
        setChallenge(null);
      } else {
        setStep("credentials");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function onChallengeVerify(input: {
    method_id?: string;
    code?: string;
    recovery_code?: string;
  }) {
    if (!challenge) return;
    setError("");
    setSubmitting(true);
    try {
      const session = await verifyMfaChallenge({
        challenge_token: challenge.challenge_token,
        ...input,
      });
      setChallenge(null);
      setStep("credentials");
      await options.onSession(session);
    } catch (cause) {
      if (isApiError(cause) && cause.code === "mfa_challenge_locked") {
        setError(mapMfaError(cause, "Verification failed."));
        setChallenge(null);
        setStep("credentials");
      } else {
        setError(mapMfaError(cause, "Verification failed."));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return {
    step,
    email,
    password,
    error,
    submitting,
    challenge,
    setEmail,
    setPassword,
    setError,
    resetToCredentials,
    onCredentialsSubmit,
    onChallengeVerify,
  };
}
