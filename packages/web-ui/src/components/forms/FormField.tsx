import type { InputHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

type FormFieldProps = {
  label: string;
  name: string;
  required?: boolean;
  className?: string;
  trailing?: ReactNode;
} & Omit<InputHTMLAttributes<HTMLInputElement>, "name" | "className">;

export function FormField({
  label,
  name,
  required,
  className,
  trailing,
  id,
  ...inputProps
}: FormFieldProps) {
  const fieldId = id ?? name;

  return (
    <div
      className={cn(
        "flex min-h-[4.5rem] items-center gap-2 rounded-full border border-border-default bg-surface px-5 py-2.5 transition-colors",
        "focus-within:border-brand focus-within:shadow-[0_0_0_3px_rgb(101_87_245_/0.12)]",
        className,
      )}
    >
      <label htmlFor={fieldId} className="m-0 grid min-w-0 flex-1 gap-0.5 font-normal">
        <span className="text-[0.75rem] leading-tight text-text-muted">
          {label}
          {required ? <span className="text-danger">*</span> : null}
        </span>
        <input
          id={fieldId}
          name={name}
          required={required}
          className="m-0 w-full border-0 bg-transparent p-0 text-[0.95rem] font-medium text-text-primary outline-none placeholder:font-normal placeholder:text-text-muted"
          {...inputProps}
        />
      </label>
      {trailing ? <div className="flex shrink-0 items-center gap-1">{trailing}</div> : null}
    </div>
  );
}
