import { FormEvent, useMemo, useState } from "react";

import { useMfaMethods } from "@/features/auth/hooks/useMfaMethods";
import { isActiveMfaMethod } from "@/features/auth/lib/mfaLabels";
import type { MfaStepUpMode } from "@/features/auth/types/auth.types";

export function useMfaSettingsPanel() {
  const mfa = useMfaMethods();

  const [totpCode, setTotpCode] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [disableTargetId, setDisableTargetId] = useState<string | null>(null);
  const [stepUpMode, setStepUpMode] = useState<MfaStepUpMode>("totp");
  const [stepUpCode, setStepUpCode] = useState("");
  const [stepUpMethodId, setStepUpMethodId] = useState("");
  const [regenOpen, setRegenOpen] = useState(false);

  const activeMethods = useMemo(
    () => mfa.methods.filter(isActiveMfaMethod),
    [mfa.methods],
  );
  const totpMethods = useMemo(
    () => activeMethods.filter((method) => method.type === "totp"),
    [activeMethods],
  );

  function resetStepUp() {
    setDisableTargetId(null);
    setRegenOpen(false);
    setStepUpCode("");
    setStepUpMode("totp");
    setStepUpMethodId(totpMethods[0]?.id ?? "");
  }

  function beginDisable(methodId: string) {
    setDisableTargetId(methodId);
    setRegenOpen(false);
    setStepUpMethodId(totpMethods[0]?.id ?? "");
    setStepUpMode(totpMethods.length ? "totp" : "recovery");
    setStepUpCode("");
  }

  function beginRegenerate() {
    setRegenOpen(true);
    setDisableTargetId(null);
    setStepUpMethodId(totpMethods[0]?.id ?? "");
    setStepUpMode(totpMethods.length ? "totp" : "recovery");
    setStepUpCode("");
  }

  async function onConfirmTotp(event: FormEvent) {
    event.preventDefault();
    try {
      await mfa.finishTotpEnroll(totpCode.trim());
      setTotpCode("");
    } catch {
      /* surfaced in hook */
    }
  }

  async function onConfirmEmail(event: FormEvent) {
    event.preventDefault();
    try {
      await mfa.finishEmailEnroll(emailCode.trim());
      setEmailCode("");
    } catch {
      /* surfaced in hook */
    }
  }

  async function onDisable(event: FormEvent) {
    event.preventDefault();
    if (!disableTargetId) return;
    try {
      if (stepUpMode === "recovery") {
        await mfa.disableMethod(disableTargetId, { recovery_code: stepUpCode.trim() });
      } else {
        await mfa.disableMethod(disableTargetId, {
          code: stepUpCode.trim(),
          verify_method_id: stepUpMethodId || totpMethods[0]?.id,
        });
      }
      resetStepUp();
    } catch {
      /* surfaced in hook */
    }
  }

  async function onRegenerate(event: FormEvent) {
    event.preventDefault();
    try {
      if (stepUpMode === "recovery") {
        await mfa.regenerateCodes({ recovery_code: stepUpCode.trim() });
      } else {
        await mfa.regenerateCodes({
          code: stepUpCode.trim(),
          method_id: stepUpMethodId || totpMethods[0]?.id,
        });
      }
      resetStepUp();
    } catch {
      /* surfaced in hook */
    }
  }

  return {
    ...mfa,
    totpCode,
    emailCode,
    disableTargetId,
    stepUpMode,
    stepUpCode,
    stepUpMethodId,
    regenOpen,
    activeMethods,
    totpMethods,
    enrolled: activeMethods.length > 0,
    setTotpCode,
    setEmailCode,
    setStepUpMode,
    setStepUpCode,
    setStepUpMethodId,
    resetStepUp,
    beginDisable,
    beginRegenerate,
    onConfirmTotp,
    onConfirmEmail,
    onDisable,
    onRegenerate,
  };
}
