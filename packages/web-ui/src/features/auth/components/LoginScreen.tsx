import { FormEvent, useState } from "react";
import { Eye, EyeOff } from "lucide-react";

import type { Portal } from "@/api";
import { AuthPortalShell } from "@/features/auth/components/AuthPortalShell";
import { MfaChallengePanel } from "@/features/auth/components/MfaChallengePanel";
import { LOGIN_COPY } from "@/features/auth/lib/loginCopy";
import type {
  LoginStep,
  MfaChallengePayload,
} from "@/features/auth/types/auth.types";

export function LoginScreen({
  portal,
  step = "credentials",
  email,
  password,
  error,
  submitting,
  challenge,
  onEmailChange,
  onPasswordChange,
  onSubmit,
  onChallengeVerify,
  onChallengeError,
  onBackToCredentials,
}: {
  portal: Portal;
  step?: LoginStep;
  email: string;
  password: string;
  error: string;
  submitting?: boolean;
  challenge?: MfaChallengePayload | null;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
  onChallengeVerify?: (input: {
    method_id?: string;
    code?: string;
    recovery_code?: string;
  }) => Promise<void>;
  onChallengeError?: (message: string) => void;
  onBackToCredentials?: () => void;
}) {
  const [showPassword, setShowPassword] = useState(false);
  const copy = LOGIN_COPY[portal];

  if (step === "privilegedBlock") {
    return (
      <AuthPortalShell heroEyebrow={copy.heroEyebrow} heroTitle={copy.heroTitle}>
        <div className="mx-auto w-full max-w-[460px]">
          <h1 className="m-0 text-[1.75rem] leading-tight font-bold tracking-[-0.02em] text-text-primary sm:text-[2.35rem]">
            MFA required
          </h1>
          <p className="mt-2 mb-6 text-[0.95rem] text-text-muted sm:mt-2.5 sm:mb-9 sm:text-[1.05rem]">
            Privileged roles cannot sign in until MFA is enrolled.
          </p>
          <p className="m-0 text-[0.95rem] text-danger" role="alert">
            {error ||
              "Contact a Super Admin for an MFA reset, or have the privileged MFA requirement disabled so you can enroll."}
          </p>
          <button
            type="button"
            className="mt-5 w-full rounded-xl bg-brand py-3 text-[1.05rem] font-semibold text-text-inverse shadow-medium sm:mt-7 sm:py-3.5"
            onClick={onBackToCredentials}
          >
            Back to sign in
          </button>
        </div>
      </AuthPortalShell>
    );
  }

  if (step === "challenge" && challenge && onChallengeVerify && onChallengeError) {
    return (
      <AuthPortalShell heroEyebrow={copy.heroEyebrow} heroTitle={copy.heroTitle}>
        <MfaChallengePanel
          challenge={challenge}
          error={error}
          submitting={submitting}
          onVerify={onChallengeVerify}
          onBack={onBackToCredentials ?? (() => undefined)}
          onError={onChallengeError}
        />
      </AuthPortalShell>
    );
  }

  return (
    <AuthPortalShell heroEyebrow={copy.heroEyebrow} heroTitle={copy.heroTitle}>
      <form
        onSubmit={onSubmit}
        className="mx-auto w-full max-w-[460px]"
        aria-labelledby="signin-heading"
        noValidate
      >
        <h1
          id="signin-heading"
          className="m-0 text-[1.75rem] leading-tight font-bold tracking-[-0.02em] text-text-primary sm:text-[2.35rem]"
        >
          {copy.title}
        </h1>
        <p className="mt-2 mb-6 text-[0.95rem] text-text-muted sm:mt-2.5 sm:mb-9 sm:text-[1.05rem]">
          {copy.subtitle}
        </p>

        <div className="grid gap-4 sm:gap-5">
          <label
            htmlFor="email"
            className="m-0 gap-2 text-[0.95rem] font-semibold text-text-primary"
          >
            Email
            <input
              id="email"
              name="email"
              type="email"
              value={email}
              onChange={(event) => onEmailChange(event.target.value)}
              autoComplete="username"
              required
              placeholder="you@company.com"
              className="w-full rounded-xl border border-border-default bg-canvas px-4 py-3 text-[0.95rem] font-normal text-text-primary outline-none placeholder:text-text-muted focus:border-brand focus:bg-surface focus:outline-none sm:py-3.5"
            />
          </label>

          <label
            htmlFor="password"
            className="m-0 gap-2 text-[0.95rem] font-semibold text-text-primary"
          >
            Password
            <span className="relative block font-normal">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => onPasswordChange(event.target.value)}
                autoComplete="current-password"
                required
                placeholder="••••••••"
                className="w-full rounded-xl border border-border-default bg-canvas py-3 pr-12 pl-4 text-[0.95rem] text-text-primary outline-none placeholder:text-text-muted focus:border-brand focus:bg-surface focus:outline-none sm:py-3.5"
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
        </div>

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
          {submitting ? "Signing in…" : "Sign in"}
        </button>

        <p className="mt-5 mb-0 text-center text-[0.9rem] text-text-muted sm:mt-8 sm:text-[0.95rem]">
          Signed-in users stay in their assigned portal only.
        </p>
      </form>
    </AuthPortalShell>
  );
}
