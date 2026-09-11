import { FormField } from "@/components/forms/FormField";

/** Agency feature wrapper — shared pill field used on create/detail forms. */
export function AgencyField({
  label,
  name,
  type = "text",
  defaultValue,
  required,
  minLength,
  autoComplete,
}: {
  label: string;
  name: string;
  type?: string;
  defaultValue?: string;
  required?: boolean;
  minLength?: number;
  autoComplete?: string;
  hint?: string;
}) {
  return (
    <FormField
      label={label}
      name={name}
      type={type}
      defaultValue={defaultValue}
      required={required}
      minLength={minLength}
      autoComplete={autoComplete}
    />
  );
}
