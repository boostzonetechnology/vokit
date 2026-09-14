import { MfaSettingsPanel } from "@/features/auth/components/MfaSettingsPanel";
import { ApiNote } from "@/features/platform/ux/ApiNote";

export function PlatformSecurityScreen() {
  return (
    <section className="mx-auto max-w-[1100px]">
      <div className="mb-6">
        <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
          Security
        </h1>
        <p className="mt-1 mb-0 text-body text-text-muted">
          Personal MFA enrollment and recovery codes for your platform account.
        </p>
      </div>
      <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
        <MfaSettingsPanel />
      </article>
      <div className="mt-4">
        <ApiNote>
          Platform catalog settings (including privileged MFA policy) remain under Settings. This
          page is for your own MFA methods only.
        </ApiNote>
      </div>
    </section>
  );
}
