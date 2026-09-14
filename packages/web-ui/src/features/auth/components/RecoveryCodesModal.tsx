import { createPortal } from "react-dom";

import { ActionButton } from "@/components/ui/ActionButton";

export function RecoveryCodesModal({
  codes,
  onAcknowledge,
}: {
  codes: string[];
  onAcknowledge: () => void;
}) {
  async function copyAll() {
    try {
      await navigator.clipboard.writeText(codes.join("\n"));
    } catch {
      // Clipboard may be unavailable; user can still copy manually.
    }
  }

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-text-primary/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="recovery-codes-title"
    >
      <div className="box-border flex w-[min(100%,28rem)] max-h-[min(90dvh,40rem)] shrink-0 flex-col overflow-hidden rounded-2xl border border-border-default bg-surface p-5 shadow-floating">
        <h2 id="recovery-codes-title" className="m-0 text-[1.15rem] font-semibold text-text-primary">
          Save your recovery codes
        </h2>
        <p className="mt-2 mb-4 text-body text-text-muted">
          Each code can be used once if you lose access to your authenticator or email. Store them
          offline. They will not be shown again.
        </p>
        <ul className="m-0 mb-4 min-h-0 flex-1 list-none overflow-y-auto rounded-xl border border-border-default bg-canvas p-3 font-mono text-body text-text-primary">
          {codes.map((code) => (
            <li key={code} className="py-0.5">
              {code}
            </li>
          ))}
        </ul>
        <div className="flex flex-wrap gap-2">
          <ActionButton variant="secondary" onClick={() => void copyAll()}>
            Copy all
          </ActionButton>
          <ActionButton onClick={onAcknowledge}>I have saved these codes</ActionButton>
        </div>
      </div>
    </div>,
    document.body,
  );
}
