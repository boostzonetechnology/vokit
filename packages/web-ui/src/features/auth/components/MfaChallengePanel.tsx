import { FormEvent, useEffect, useState } from "react";

import { isApiError } from "@/api";
import { sendMfaChallenge } from "@/features/auth/services/mfa.service";
import type { MfaChallengePayload } from "@/features/auth/types/auth.types";

export function MfaChallengePanel({
  challenge,
  error,
  submitting,
  onVerify,
  onBack,
  onError,
}: {
  challenge: MfaChallengePayload;
  error: string;
  submitting?: boolean;
  onVerify: (input: {
    method_id?: string;
    code?: string;
    recovery_code?: string;
  }) => Promise<void>;
  onBack: () => void;
  onError: (message: string) => void;
}) {
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
      onError(
        isApiError(cause)
          ? cause.message || "Could not send email code."
          : "Could not send email code.",
      );
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

  return (
    <form
      onSubmit={(event) => void onSubmit(event)}
      className="mx-auto w-full max-w-[460px]"
      aria-labelledby="mfa-challenge-heading"
      noValidate
    >
      <h1
        id="mfa-challenge-heading"
        className="m-0 text-[1.75rem] leading-tight font-bold tracking-[-0.02em] text-text-primary sm:text-[2.35rem]"
      >
        Verify identity
      </h1>
      <p className="mt-2 mb-6 text-[0.95rem] text-text-muted sm:mt-2.5 sm:mb-9 sm:text-[1.05rem]">
        Enter a verification code to finish signing in.
      </p>

      {!useRecovery ? (
        <div className="grid gap-4 sm:gap-5">
          {methods.length > 1 ? (
            <label className="m-0 gap-2 text-[0.95rem] font-semibold text-text-primary">
              Method
              <select
                value={methodId}
                onChange={(event) => {
                  setMethodId(event.target.value);
                  setCode("");
                  setEmailSent(false);
                }}
                className="w-full rounded-xl border border-border-default bg-canvas px-4 py-3 text-[0.95rem] font-normal text-text-primary outline-none focus:border-brand focus:bg-surface"
              >
                {methods.map((method) => (
                  <option key={method.id} value={method.id}>
                    {method.type === "totp"
                      ? "Authenticator app"
                      : `Email${method.email_hint ? ` (${method.email_hint})` : ""}`}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <p className="m-0 text-[0.95rem] text-text-muted">
              {selected?.type === "totp"
                ? "Use your authenticator app."
                : `Email code${selected?.email_hint ? ` to ${selected.email_hint}` : ""}.`}
            </p>
          )}

          {selected?.type === "email" ? (
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                disabled={sending || submitting}
                onClick={() => void onSendEmail()}
                className="rounded-xl border border-border-default bg-canvas px-4 py-2.5 text-[0.95rem] font-semibold text-text-primary disabled:opacity-60"
              >
                {sending ? "Sending…" : emailSent ? "Resend code" : "Send code"}
              </button>
              {emailSent ? (
                <span className="text-[0.9rem] text-text-muted">Code sent. Check your inbox.</span>
              ) : null}
            </div>
          ) : null}

          <label className="m-0 gap-2 text-[0.95rem] font-semibold text-text-primary">
            Verification code
            <input
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={code}
              onChange={(event) => setCode(event.target.value)}
              required={!useRecovery}
              placeholder="123456"
              className="w-full rounded-xl border border-border-default bg-canvas px-4 py-3 text-[0.95rem] font-normal text-text-primary outline-none placeholder:text-text-muted focus:border-brand focus:bg-surface"
            />
          </label>
        </div>
      ) : (
        <label className="m-0 gap-2 text-[0.95rem] font-semibold text-text-primary">
          Recovery code
          <input
            type="text"
            autoComplete="off"
            value={recoveryCode}
            onChange={(event) => setRecoveryCode(event.target.value)}
            required={useRecovery}
            placeholder="xxxx-xxxx-xxxx"
            className="w-full rounded-xl border border-border-default bg-canvas px-4 py-3 text-[0.95rem] font-normal text-text-primary outline-none placeholder:text-text-muted focus:border-brand focus:bg-surface"
          />
        </label>
      )}

      {error ? (
        <p className="mt-4 text-[0.95rem] text-danger" role="alert">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={submitting}
        className="mt-5 w-full rounded-xl bg-brand py-3 text-[1.05rem] font-semibold text-text-inverse shadow-medium transition-opacity disabled:opacity-60 sm:mt-7 sm:py-3.5"
      >
        {submitting ? "Verifying…" : "Verify"}
      </button>

      <div className="mt-5 flex flex-col items-center gap-2 sm:mt-8">
        <button
          type="button"
          className="border-0 bg-transparent p-0 text-[0.9rem] font-medium text-brand underline-offset-2 hover:underline"
          onClick={() => {
            setUseRecovery((value) => !value);
            onError("");
          }}
        >
          {useRecovery ? "Use authenticator or email code" : "Use a recovery code"}
        </button>
        <button
          type="button"
          className="border-0 bg-transparent p-0 text-[0.9rem] text-text-muted underline-offset-2 hover:underline"
          onClick={onBack}
        >
          Back to sign in
        </button>
      </div>
    </form>
  );
}
