import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "outline";

const VARIANT: Record<Variant, string> = {
  primary: "border-transparent bg-brand text-text-inverse hover:opacity-90",
  secondary: "border-transparent bg-canvas text-text-primary hover:bg-brand-subtle",
  outline: "border-brand bg-surface text-text-brand hover:bg-brand-subtle",
};

export function ActionButton({
  children,
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center rounded-xl border px-3.5 py-2.5 text-body font-semibold transition-colors disabled:opacity-50",
        VARIANT[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
