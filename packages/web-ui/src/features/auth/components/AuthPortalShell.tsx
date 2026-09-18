import type { ReactNode } from "react";

import loginHeroImage from "@/assets/login-form.jpg";

export function AuthPortalShell({
  heroEyebrow,
  heroTitle,
  children,
}: {
  heroEyebrow: string;
  heroTitle: string;
  children: ReactNode;
}) {
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
                {heroEyebrow}
              </p>
              <h2 className="m-0 text-[1.35rem] leading-[1.2] font-bold tracking-[-0.02em] text-text-inverse sm:text-[1.85rem] lg:text-[2.2rem]">
                {heroTitle}
              </h2>
            </div>
          </div>
        </section>

        <section className="relative flex min-h-0 flex-col justify-center overflow-hidden px-4 py-5 sm:px-10 sm:py-8 lg:px-14 lg:py-10">
          <div className="min-h-0 overflow-y-auto">{children}</div>
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
