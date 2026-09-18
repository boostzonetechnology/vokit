import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

import { cn } from "@/lib/utils";

/** Full-width stacked field for agency detail/admin forms (not the create-wizard pill). */
export function AgencyStackField({
  label,
  name,
  required,
  className,
  hint,
  ...inputProps
}: {
  label: string;
  name: string;
  required?: boolean;
  className?: string;
  hint?: string;
} & Omit<InputHTMLAttributes<HTMLInputElement>, "name" | "className">) {
  const fieldId = inputProps.id ?? name;
  return (
    <label htmlFor={fieldId} className={cn("m-0 grid w-full min-w-0 gap-1.5 font-normal", className)}>
      <span className="text-body-sm text-text-muted">
        {label}
        {required ? <span className="text-danger">*</span> : null}
      </span>
      <input
        id={fieldId}
        name={name}
        required={required}
        className="w-full min-w-0 rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body text-text-primary outline-none focus:border-brand"
        {...inputProps}
      />
      {hint ? <span className="text-body-sm text-text-muted">{hint}</span> : null}
    </label>
  );
}

export function AgencyStackTextarea({
  label,
  name,
  required,
  className,
  hint,
  children,
  ...textareaProps
}: {
  label: string;
  name: string;
  required?: boolean;
  className?: string;
  hint?: string;
  children?: ReactNode;
} & Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "name" | "className">) {
  const fieldId = textareaProps.id ?? name;
  return (
    <label htmlFor={fieldId} className={cn("m-0 grid w-full min-w-0 gap-1.5 font-normal", className)}>
      <span className="text-body-sm text-text-muted">
        {label}
        {required ? <span className="text-danger">*</span> : null}
      </span>
      <textarea
        id={fieldId}
        name={name}
        required={required}
        className="w-full min-w-0 resize-y rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body text-text-primary outline-none focus:border-brand"
        {...textareaProps}
      />
      {hint ? <span className="text-body-sm text-text-muted">{hint}</span> : null}
      {children}
    </label>
  );
}

export function AgencyStackSelect({
  label,
  name,
  required,
  className,
  children,
  ...selectProps
}: {
  label: string;
  name?: string;
  required?: boolean;
  className?: string;
  children: ReactNode;
} & Omit<SelectHTMLAttributes<HTMLSelectElement>, "name" | "className" | "children">) {
  const fieldId = selectProps.id ?? name ?? label;
  return (
    <label htmlFor={fieldId} className={cn("m-0 grid w-full min-w-0 gap-1.5 font-normal", className)}>
      <span className="text-body-sm text-text-muted">
        {label}
        {required ? <span className="text-danger">*</span> : null}
      </span>
      <select
        id={fieldId}
        name={name}
        required={required}
        className="w-full min-w-0 rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body text-text-primary outline-none focus:border-brand"
        {...selectProps}
      >
        {children}
      </select>
    </label>
  );
}
