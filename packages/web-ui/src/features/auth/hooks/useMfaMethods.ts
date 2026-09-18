import { useCallback, useEffect, useState } from "react";

import { mapMfaError } from "@/features/auth/lib/mapMfaError";
import {
  confirmEmail,
  confirmTotp,
  disableMfaMethod,
  enrollEmail,
  enrollTotp,
  listMfaMethods,
  regenerateRecoveryCodes,
} from "@/features/auth/services/mfa.service";
import type {
  EmailEnrollResult,
  MfaMethodRecord,
  TotpEnrollResult,
} from "@/features/auth/types/auth.types";

export function useMfaMethods() {
  const [methods, setMethods] = useState<MfaMethodRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [totpEnroll, setTotpEnroll] = useState<TotpEnrollResult | null>(null);
  const [emailEnroll, setEmailEnroll] = useState<EmailEnrollResult | null>(null);
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const rows = await listMfaMethods();
      setMethods(rows);
    } catch (cause) {
      setError(mapMfaError(cause, "Failed to load MFA methods."));
      setMethods([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function startTotpEnroll() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await enrollTotp();
      setTotpEnroll(result);
      setEmailEnroll(null);
    } catch (cause) {
      setError(mapMfaError(cause, "Could not start authenticator enrollment."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function finishTotpEnroll(code: string) {
    if (!totpEnroll) return;
    setBusy(true);
    setError("");
    try {
      const result = await confirmTotp({ method_id: totpEnroll.method_id, code });
      setTotpEnroll(null);
      if (result.recovery_codes?.length) {
        setRecoveryCodes(result.recovery_codes);
      }
      setMessage("Authenticator app enrolled.");
      await reload();
    } catch (cause) {
      setError(mapMfaError(cause, "Invalid authenticator code."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function startEmailEnroll() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await enrollEmail();
      setEmailEnroll(result);
      setTotpEnroll(null);
      setMessage("Email code sent. Enter it below to confirm.");
    } catch (cause) {
      setError(mapMfaError(cause, "Could not start email enrollment."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function finishEmailEnroll(code: string) {
    if (!emailEnroll) return;
    setBusy(true);
    setError("");
    try {
      const result = await confirmEmail({
        method_id: emailEnroll.method_id,
        challenge_token: emailEnroll.challenge_token,
        code,
      });
      setEmailEnroll(null);
      if (result.recovery_codes?.length) {
        setRecoveryCodes(result.recovery_codes);
      }
      setMessage("Email MFA enrolled.");
      await reload();
    } catch (cause) {
      setError(mapMfaError(cause, "Invalid email code."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function disableMethod(
    methodId: string,
    input: { code?: string; verify_method_id?: string; recovery_code?: string },
  ) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await disableMfaMethod(methodId, input);
      setMessage("MFA method disabled.");
      await reload();
    } catch (cause) {
      setError(mapMfaError(cause, "Could not disable MFA method."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function regenerateCodes(input: {
    code?: string;
    method_id?: string;
    recovery_code?: string;
  }) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const codes = await regenerateRecoveryCodes(input);
      setRecoveryCodes(codes);
      setMessage("New recovery codes generated. Store them securely.");
    } catch (cause) {
      setError(mapMfaError(cause, "Could not regenerate recovery codes."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  function clearRecoveryCodes() {
    setRecoveryCodes(null);
  }

  function cancelEnroll() {
    setTotpEnroll(null);
    setEmailEnroll(null);
  }

  return {
    methods,
    loading,
    busy,
    error,
    message,
    totpEnroll,
    emailEnroll,
    recoveryCodes,
    reload,
    startTotpEnroll,
    finishTotpEnroll,
    startEmailEnroll,
    finishEmailEnroll,
    disableMethod,
    regenerateCodes,
    clearRecoveryCodes,
    cancelEnroll,
    setError,
    setMessage,
  };
}
