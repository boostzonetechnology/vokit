import { FormEvent, useState } from "react";
import { Eye, EyeOff } from "lucide-react";

import type { Portal } from "@/api";
import loginHeroImage from "@/assets/login-form.jpg";

const PORTAL_COPY: Record<
  Portal,
  { title: string; subtitle: string; heroEyebrow: string; heroTitle: string }
> = {
  platform: {
    title: "Sign in",
    subtitle: "Access the Platform control plane",
    heroEyebrow: "Platform portal",
    heroTitle: "Log in to your personal account to access all features.",
  },
  agency: {
    title: "Sign in",
    subtitle: "Access your Agency workspace",
    heroEyebrow: "Agency portal",
    heroTitle: "Log in to your personal account to access all features.",
  },
  customer: {
    title: "Sign in",
    subtitle: "Access your Customer workspace",
    heroEyebrow: "Customer portal",
    heroTitle: "Log in to your personal account to access all features.",
  },
};

export function LoginScreen({
  portal,
  email,
  password,
  error,
  submitting,
  onEmailChange,
  onPasswordChange,
  onSubmit,
}: {
  portal: Portal;
  email: string;
  password: string;
  error: string;
  submitting?: boolean;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
}) {
  const [showPassword, setShowPassword] = useState(false);
  const copy = PORTAL_COPY[portal];

  return (
    <div className="box-border flex h-dvh w-full items-center justify-center overflow-hidden bg-canvas p-3 sm:p-5 lg:p-8">
      <main
        id="main"
        className="relative grid h-full max-h-[min(42.5rem,100%)] w-full max-w-[1180px] grid-rows-[minmax(8.5rem,30%)_minmax(0,1fr)] gap-0 overflow-hidden rounded-[28px] border border-border-default bg-surface p-2.5 shadow-floating sm:p-3 lg:grid-cols-[minmax(340px,0.92fr)_1.2fr] lg:grid-rows-none"
      >
        <section className="relative min-h-0 overflow-hidden rounded-[22px]">
          <img
            src={loginHeroImage}
            alt=""
            className="absolute inset-0 size-full object-cover"
          />
          <div
            className="absolute inset-0 bg-gradient-to-t from-text-primary/70 via-text-primary/25 to-text-primary/10"
            aria-hidden
          />

          <div className="relative flex h-full flex-col justify-between p-5 sm:p-7 lg:p-9">
            <div className="flex items-center gap-3">
              <span className="inline-flex size-9 items-center justify-center rounded-full bg-surface text-base font-bold text-brand">
                v
              </span>
              <span className="text-[1.35rem] font-semibold tracking-tight text-text-inverse">
                Vokit
              </span>
            </div>

            <div className="max-w-[22rem] pb-1">
              <p className="m-0 mb-2 text-[0.9rem] font-medium text-text-inverse/80 sm:mb-3 sm:text-[0.95rem]">
                {copy.heroEyebrow}
              </p>
              <h2 className="m-0 text-[1.35rem] leading-[1.2] font-bold tracking-[-0.02em] text-text-inverse sm:text-[1.85rem] lg:text-[2.2rem]">
                {copy.heroTitle}
              </h2>
            </div>
          </div>
        </section>

        <section className="relative flex min-h-0 flex-col justify-center overflow-hidden px-4 py-5 sm:px-10 sm:py-8 lg:px-14 lg:py-10">
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

          <span
            className="absolute right-4 bottom-4 inline-flex size-8 items-center justify-center rounded-lg bg-brand-subtle text-sm font-bold text-brand sm:right-5 sm:bottom-5"
            aria-hidden
          >
            v
          </span>
        </section>
      </main>
    </div>
  );
}
