import { Check, Copy, Eye, EyeOff, RefreshCw } from "lucide-react";
import { useState } from "react";

import { FormField } from "@/components/forms/FormField";
import { generateSecurePassword } from "@/lib/password";
import { cn } from "@/lib/utils";

type PasswordInputProps = {
  label: string;
  name: string;
  required?: boolean;
  minLength?: number;
  value: string;
  onChange: (value: string) => void;
  className?: string;
};

export function PasswordInput({
  label,
  name,
  required,
  minLength = 12,
  value,
  onChange,
  className,
}: PasswordInputProps) {
  const [visible, setVisible] = useState(false);
  const [copied, setCopied] = useState(false);

  async function copyPassword() {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  function generate() {
    const next = generateSecurePassword(20);
    onChange(next);
    setVisible(true);
    setCopied(false);
  }

  return (
    <div className={cn("grid gap-2", className)}>
      <FormField
        label={label}
        name={name}
        type={visible ? "text" : "password"}
        required={required}
        minLength={minLength}
        autoComplete="new-password"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        trailing={
          <>
            <IconAction
              label={visible ? "Hide password" : "Show password"}
              onClick={() => setVisible((v) => !v)}
            >
              {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </IconAction>
            <IconAction label="Copy password" onClick={() => void copyPassword()} disabled={!value}>
              {copied ? <Check className="size-4 text-success" /> : <Copy className="size-4" />}
            </IconAction>
          </>
        }
      />
      <div className="flex flex-wrap items-center gap-2 px-1">
        <button
          type="button"
          onClick={generate}
          className="inline-flex items-center gap-1.5 rounded-full border border-border-default bg-surface px-3.5 py-1.5 text-body-sm font-semibold text-text-brand transition-colors hover:bg-brand-subtle"
        >
          <RefreshCw className="size-3.5" aria-hidden />
          Generate password
        </button>
        {copied ? (
          <span className="text-body-sm font-medium text-success" role="status">
            Copied
          </span>
        ) : null}
      </div>
    </div>
  );
}

function IconAction({
  label,
  onClick,
  disabled,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
      className="inline-flex size-9 items-center justify-center rounded-full text-text-muted transition-colors hover:bg-canvas hover:text-text-primary disabled:opacity-40"
    >
      {children}
    </button>
  );
}
