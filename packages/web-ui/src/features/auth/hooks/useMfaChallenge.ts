import { FormEvent, useEffect, useState } from "react";

import { mapMfaError } from "@/features/auth/lib/mapMfaError";
import { sendMfaChallenge } from "@/features/auth/services/mfa.service";
import type { MfaChallengePayload } from "@/features/auth/types/auth.types";

export function useMfaChallenge(options: {
  challenge: MfaChallengePayload;
  onVerify: (input: {
    method_id?: string;
    code?: string;
    recovery_code?: string;
  }) => Promise<void>;
  onError: (message: string) => void;
}) {
  const { challenge, onVerify, onError } = options;
  const methods = challenge.methods;

  const [methodId, setMethodId] = useState(methods[0]?.id ?? "");
  const [code, setCode] = useState("");
  const [recoveryCode, setRecoveryCode] = useState("");
  const [useRecovery, setUseRecovery] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [sending, setSending] = useState(false);

  const selected = methods.find((method) => method.id === methodId) ?? methods[0];

  useEffect(() => {
    setMethodId(challenge.methods[0]?.id ?? "");
    setCode("");
    setRecoveryCode("");
    setUseRecovery(false);
    setEmailSent(false);
  }, [challenge.challenge_token]);

  function selectMethod(nextMethodId: string) {
    setMethodId(nextMethodId);
    setCode("");
    setEmailSent(false);
  }

  function toggleRecovery() {
    setUseRecovery((value) => !value);
    onError("");
  }

  async function onSendEmail() {
    if (!selected || selected.type !== "email") return;
    setSending(true);
    onError("");
    try {
      await sendMfaChallenge({
        challenge_token: challenge.challenge_token,
        method_id: selected.id,
      });
      setEmailSent(true);
    } catch (cause) {
      onError(mapMfaError(cause, "Could not send email code."));
    } finally {
      setSending(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (useRecovery) {
      await onVerify({ recovery_code: recoveryCode.trim() });
      return;
    }
    if (!selected) return;
    await onVerify({ method_id: selected.id, code: code.trim() });
  }

  return {
    methods,
    selected,
    methodId,
    code,
    recoveryCode,
    useRecovery,
    emailSent,
    sending,
    setCode,
    setRecoveryCode,
    selectMethod,
    toggleRecovery,
    onSendEmail,
    onSubmit,
  };
}
