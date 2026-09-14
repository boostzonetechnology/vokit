import { QRCodeSVG } from "qrcode.react";

import { ActionButton } from "@/components/ui/ActionButton";

export function TotpEnrollPreview({
  otpauthUri,
  secret,
}: {
  otpauthUri: string;
  secret: string;
}) {
  async function copySecret() {
    try {
      await navigator.clipboard.writeText(secret);
    } catch {
      // Clipboard may be unavailable.
    }
  }

  return (
    <div className="mb-4 grid gap-4 sm:grid-cols-[auto_1fr] sm:items-start">
      <div className="inline-flex rounded-xl border border-border-default bg-surface p-3">
        <QRCodeSVG
          value={otpauthUri}
          size={168}
          level="M"
          marginSize={1}
          title="Authenticator QR code"
          aria-label="Scan this QR code with your authenticator app"
        />
      </div>
      <div className="min-w-0">
        <p className="m-0 text-sm text-text-muted">
          Scan this QR code with Google Authenticator, Authy, or a similar app. If you cannot scan,
          enter the secret manually.
        </p>
        <label className="mt-3 m-0 grid gap-1.5 font-normal">
          <span className="text-body-sm text-text-muted">Secret</span>
          <div className="flex flex-wrap items-center gap-2">
            <code className="min-w-0 flex-1 break-all rounded-xl border border-border-default bg-surface px-3 py-2.5 font-mono text-sm text-text-primary">
              {secret}
            </code>
            <ActionButton type="button" variant="outline" onClick={() => void copySecret()}>
              Copy
            </ActionButton>
          </div>
        </label>
      </div>
    </div>
  );
}
