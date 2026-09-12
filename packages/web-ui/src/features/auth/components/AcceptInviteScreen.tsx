import { FormEvent, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";

import { apiSend, isApiError, type Portal } from "@/api";
import loginHeroImage from "@/assets/login-form.jpg";

const PORTAL_COPY: Record<
  Portal,
  { eyebrow: string; heroTitle: string; subtitle: string }
> = {
  platform: {
    eyebrow: "Platform invitation",
    heroTitle: "Finish setup to access the Vokit control plane.",
    subtitle: "Create your password to join the platform workspace.",
  },
  agency: {
    eyebrow: "Agency invitation",
    heroTitle: "Finish setup to access your agency workspace.",
    subtitle: "Create your password to join this agency on Vokit.",
  },
  customer: {
    eyebrow: "Customer invitation",
    heroTitle: "Finish setup to access your customer workspace.",
    subtitle: "Create your password to join this customer account.",
  },
};

export function AcceptInviteScreen({ portal }: { portal: Portal }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = useMemo(() => (params.get("token") || "").trim(), [params]);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const copy = PORTAL_COPY[portal];

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!token) {
      setError("Invitation link is missing a token. Open the button from your email again.");
      return;
    }
    if (password.length < 12) {
      setError("Password must be at least 12 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await apiSend("/api/v1/auth/invitations/accept", "POST", { token, password });
      setMessage("Invitation accepted. Redirecting to sign in…");
      window.setTimeout(() => navigate("/", { replace: true }), 900);
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Could not accept invitation.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4 py-8 sm:px-6 lg:px-10">
      <main
        id="main"
        className="relative grid w-full max-w-[1180px] gap-0 overflow-hidden rounded-[28px] border border-border-default bg-surface p-3 shadow-floating lg:grid-cols-[minmax(380px,0.92fr)_1.2fr]"
      >
        <section className="relative min-h-[240px] overflow-hidden rounded-[22px] lg:min-h-[640px]">
          <img
            src={loginHeroImage}
            alt=""
            className="absolute inset-0 size-full object-cover"
          />
          <div
            className="absolute inset-0 bg-gradient-to-t from-text-primary/70 via-text-primary/25 to-text-primary/10"
            aria-hidden
          />
          <div className="relative flex h-full min-h-[240px] flex-col justify-between p-7 sm:p-8 lg:min-h-[640px] lg:p-9">
            <div className="flex items-center gap-3">
              <span className="inline-flex size-9 items-center justify-center rounded-full bg-surface text-base font-bold text-brand">
                v
              </span>
              <span className="text-[1.35rem] font-semibold tracking-tight text-text-inverse">
                Vokit
              </span>
            </div>
            <div className="max-w-[24rem] pb-1">
              <p className="m-0 mb-3 text-[0.95rem] font-medium text-text-inverse/80">
                {copy.eyebrow}
              </p>
              <h2 className="m-0 text-[1.85rem] leading-[1.2] font-bold tracking-[-0.02em] text-text-inverse sm:text-[2.2rem]">
                {copy.heroTitle}
              </h2>
            </div>
          </div>
        </section>

        <section className="relative flex flex-col justify-center px-5 py-8 sm:px-10 lg:px-14 lg:py-10">
          <form
            onSubmit={(event) => void onSubmit(event)}
            className="mx-auto w-full max-w-[460px]"
            aria-labelledby="accept-invite-heading"
            noValidate
          >
            <h1
              id="accept-invite-heading"
              className="m-0 text-[2rem] leading-tight font-bold tracking-[-0.02em] text-text-primary sm:text-[2.35rem]"
            >
              Accept invitation
            </h1>
            <p className="mt-2.5 mb-9 text-[1.05rem] text-text-muted">{copy.subtitle}</p>

            <div className="grid gap-5">
              <label
                htmlFor="invite-password"
                className="m-0 grid gap-2 text-[0.95rem] font-semibold text-text-primary"
              >
                Password
                <span className="relative block font-normal">
                  <input
                    id="invite-password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="new-password"
                    required
                    minLength={12}
                    placeholder="At least 12 characters"
                    className="w-full rounded-xl border border-border-default bg-canvas py-3.5 pr-12 pl-4 text-[0.95rem] text-text-primary outline-none placeholder:text-text-muted focus:border-brand focus:bg-surface focus:outline-none"
                  />
                  <button
                    type="button"
                    className="absolute top-1/2 right-2.5 inline-flex size-9 -translate-y-1/2 items-center justify-center rounded-lg bg-transparent text-text-muted hover:text-text-primary"
                    onClick={() => setShowPassword((value) => !value)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                  </button>
                </span>
              </label>

              <label
                htmlFor="invite-confirm"
                className="m-0 grid gap-2 text-[0.95rem] font-semibold text-text-primary"
              >
                Confirm password
                <input
                  id="invite-confirm"
                  name="confirm_password"
                  type={showPassword ? "text" : "password"}
                  value={confirm}
                  onChange={(event) => setConfirm(event.target.value)}
                  autoComplete="new-password"
                  required
                  minLength={12}
                  placeholder="Re-enter password"
                  className="w-full rounded-xl border border-border-default bg-canvas px-4 py-3.5 text-[0.95rem] font-normal text-text-primary outline-none placeholder:text-text-muted focus:border-brand focus:bg-surface focus:outline-none"
                />
              </label>
            </div>

            {!token ? (
              <p className="mt-4 text-[0.95rem] text-danger" role="alert">
                This invite link is incomplete. Open the button from your email again.
              </p>
            ) : null}
            {error ? (
              <p className="mt-4 text-[0.95rem] text-danger" role="alert">
                {error}
              </p>
            ) : null}
            {message ? (
              <p className="mt-4 text-[0.95rem] text-text-brand" role="status">
                {message}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={busy || !token}
              className="mt-7 w-full rounded-xl bg-brand py-3.5 text-[1.05rem] font-semibold text-text-inverse shadow-medium transition-opacity disabled:opacity-60"
            >
              {busy ? "Accepting…" : "Accept invitation"}
            </button>

            <p className="mt-8 mb-0 text-center text-[0.95rem] text-text-muted">
              After accepting, sign in with this email and your new password.
            </p>
          </form>

          <span
            className="absolute right-5 bottom-5 inline-flex size-8 items-center justify-center rounded-lg bg-brand-subtle text-sm font-bold text-brand"
            aria-hidden
          >
            v
          </span>
        </section>
      </main>
    </div>
  );
}
