import { ActionButton } from "@/components/ui/ActionButton";
import { FormSectionSkeleton } from "@/components/ui/FormSectionSkeleton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { RecoveryCodesModal } from "@/features/auth/components/RecoveryCodesModal";
import { TotpEnrollPreview } from "@/features/auth/components/TotpEnrollPreview";
import { useMfaSettingsPanel } from "@/features/auth/hooks/useMfaSettingsPanel";
import { mfaMethodTitle } from "@/features/auth/lib/mfaLabels";
import { ApiNote } from "@/features/platform/ux/ApiNote";

export function MfaSettingsPanel() {
  const {
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
    startEmailEnroll,
    cancelEnroll,
    clearRecoveryCodes,
    totpCode,
    emailCode,
    disableTargetId,
    stepUpMode,
    stepUpCode,
    stepUpMethodId,
    regenOpen,
    activeMethods,
    totpMethods,
    enrolled,
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
  } = useMfaSettingsPanel();

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="m-0 text-[1.05rem] font-semibold text-text-primary">Multi-factor authentication</h2>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Protect your account with an authenticator app and/or email codes.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge tone={enrolled ? "success" : "warning"}>
            {enrolled ? "MFA enrolled" : "MFA not enrolled"}
          </StatusBadge>
          <ActionButton variant="secondary" disabled={loading || busy} onClick={() => void reload()}>
            Refresh
          </ActionButton>
        </div>
      </div>

      {error ? (
        <p className="m-0 text-danger" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="m-0 text-body text-text-brand" role="status">
          {message}
        </p>
      ) : null}

      {loading && methods.length === 0 ? (
        <FormSectionSkeleton fields={4} />
      ) : (
        <ul className="m-0 grid list-none gap-2 p-0">
          {!activeMethods.length ? (
            <li className="rounded-xl border border-border-default bg-canvas px-3 py-3 text-body text-text-muted">
              No active MFA methods yet.
            </li>
          ) : (
            activeMethods.map((method) => (
              <li
                key={method.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border-default bg-canvas px-3 py-3"
              >
                <div>
                  <p className="m-0 font-medium text-text-primary">
                    {mfaMethodTitle(method.type)}
                  </p>
                  <p className="m-0 text-sm text-text-muted">
                    {method.email_hint || method.id.slice(0, 8)}
                    {method.verified_at ? ` · verified ${method.verified_at}` : ""}
                  </p>
                </div>
                <ActionButton
                  variant="outline"
                  disabled={busy}
                  onClick={() => beginDisable(method.id)}
                >
                  Disable
                </ActionButton>
              </li>
            ))
          )}
        </ul>
      )}

      <div className="flex flex-wrap gap-2">
        <ActionButton
          disabled={busy || Boolean(totpEnroll)}
          onClick={() => void startTotpEnroll()}
        >
          Enroll authenticator
        </ActionButton>
        <ActionButton
          variant="secondary"
          disabled={busy || Boolean(emailEnroll)}
          onClick={() => void startEmailEnroll()}
        >
          Enroll email
        </ActionButton>
        <ActionButton
          variant="outline"
          disabled={busy || !activeMethods.length}
          onClick={beginRegenerate}
        >
          Regenerate recovery codes
        </ActionButton>
      </div>

      {totpEnroll ? (
        <article className="rounded-xl border border-border-default bg-canvas p-4">
          <h3 className="m-0 mb-2 text-body font-semibold text-text-primary">
            Confirm authenticator
          </h3>
          <p className="mt-0 mb-3 text-sm text-text-muted">
            Scan the QR code below, or enter the secret manually, then confirm with a 6-digit code
            from your authenticator app.
          </p>
          <TotpEnrollPreview otpauthUri={totpEnroll.otpauth_uri} secret={totpEnroll.secret} />
          <form className="flex flex-wrap items-end gap-2" onSubmit={(event) => void onConfirmTotp(event)}>
            <label className="m-0 grid min-w-[12rem] flex-1 gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Authenticator code</span>
              <input
                value={totpCode}
                onChange={(event) => setTotpCode(event.target.value)}
                required
                inputMode="numeric"
                autoComplete="one-time-code"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <ActionButton type="submit" disabled={busy}>
              Confirm
            </ActionButton>
            <ActionButton type="button" variant="outline" disabled={busy} onClick={cancelEnroll}>
              Cancel
            </ActionButton>
          </form>
        </article>
      ) : null}

      {emailEnroll ? (
        <article className="rounded-xl border border-border-default bg-canvas p-4">
          <h3 className="m-0 mb-2 text-body font-semibold text-text-primary">Confirm email MFA</h3>
          <p className="mt-0 mb-3 text-sm text-text-muted">
            Enter the one-time code sent to your account email. Expires in about{" "}
            {emailEnroll.expires_in} seconds.
          </p>
          <form className="flex flex-wrap items-end gap-2" onSubmit={(event) => void onConfirmEmail(event)}>
            <label className="m-0 grid min-w-[12rem] flex-1 gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">Email code</span>
              <input
                value={emailCode}
                onChange={(event) => setEmailCode(event.target.value)}
                required
                inputMode="numeric"
                autoComplete="one-time-code"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <ActionButton type="submit" disabled={busy}>
              Confirm
            </ActionButton>
            <ActionButton type="button" variant="outline" disabled={busy} onClick={cancelEnroll}>
              Cancel
            </ActionButton>
          </form>
        </article>
      ) : null}

      {disableTargetId || regenOpen ? (
        <article className="rounded-xl border border-border-default bg-canvas p-4">
          <h3 className="m-0 mb-2 text-body font-semibold text-text-primary">
            {regenOpen ? "Confirm recovery code regeneration" : "Confirm MFA disable"}
          </h3>
          <p className="mt-0 mb-3 text-sm text-text-muted">
            Step-up verification is required. Use a TOTP code from an enrolled authenticator, or a
            recovery code.
          </p>
          <form
            className="grid max-w-lg gap-3"
            onSubmit={(event) => void (regenOpen ? onRegenerate(event) : onDisable(event))}
          >
            <div className="flex flex-wrap gap-2">
              <ActionButton
                type="button"
                variant={stepUpMode === "totp" ? "secondary" : "outline"}
                disabled={!totpMethods.length}
                onClick={() => setStepUpMode("totp")}
              >
                Authenticator
              </ActionButton>
              <ActionButton
                type="button"
                variant={stepUpMode === "recovery" ? "secondary" : "outline"}
                onClick={() => setStepUpMode("recovery")}
              >
                Recovery code
              </ActionButton>
            </div>
            {stepUpMode === "totp" && totpMethods.length > 1 ? (
              <label className="m-0 grid gap-1.5 font-normal">
                <span className="text-body-sm text-text-muted">Authenticator method</span>
                <select
                  value={stepUpMethodId}
                  onChange={(event) => setStepUpMethodId(event.target.value)}
                  className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
                >
                  {totpMethods.map((method) => (
                    <option key={method.id} value={method.id}>
                      {method.id.slice(0, 8)}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <label className="m-0 grid gap-1.5 font-normal">
              <span className="text-body-sm text-text-muted">
                {stepUpMode === "recovery" ? "Recovery code" : "Authenticator code"}
              </span>
              <input
                value={stepUpCode}
                onChange={(event) => setStepUpCode(event.target.value)}
                required
                autoComplete="off"
                className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <ActionButton type="submit" disabled={busy}>
                {regenOpen ? "Regenerate" : "Disable method"}
              </ActionButton>
              <ActionButton type="button" variant="outline" disabled={busy} onClick={resetStepUp}>
                Cancel
              </ActionButton>
            </div>
          </form>
        </article>
      ) : null}

      <ApiNote>
        Login challenges use TOTP, email OTP, or a one-time recovery code. Disabling the last method
        is blocked when privileged MFA is required for your role.
      </ApiNote>

      {recoveryCodes?.length ? (
        <RecoveryCodesModal codes={recoveryCodes} onAcknowledge={clearRecoveryCodes} />
      ) : null}
    </div>
  );
}
