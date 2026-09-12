import type { SelectHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type FormSelectProps = {
  label: string;
  name: string;
  required?: boolean;
  className?: string;
  children: React.ReactNode;
} & Omit<SelectHTMLAttributes<HTMLSelectElement>, "name" | "className">;

export function FormSelect({
  label,
  name,
  required,
  className,
  children,
  id,
  ...selectProps
}: FormSelectProps) {
  const fieldId = id ?? name;

  return (
    <div
      className={cn(
        "flex min-h-[4.5rem] items-center rounded-full border border-border-default bg-surface px-5 py-2.5 transition-colors",
        "focus-within:border-brand focus-within:shadow-[0_0_0_3px_rgb(101_87_245_/0.12)]",
        className,
      )}
    >
      <label htmlFor={fieldId} className="m-0 grid min-w-0 flex-1 gap-0.5 font-normal">
        <span className="text-[0.75rem] leading-tight text-text-muted">
          {label}
          {required ? <span className="text-danger">*</span> : null}
        </span>
        <select
          id={fieldId}
          name={name}
          required={required}
          className="m-0 w-full cursor-pointer border-0 bg-transparent p-0 text-[0.95rem] font-medium text-text-primary outline-none"
          {...selectProps}
        >
          {children}
        </select>
      </label>
    </div>
  );
}
