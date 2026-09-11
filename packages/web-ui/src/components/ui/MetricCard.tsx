import { cn } from "../../lib/utils";

export type MetricAccent = "brand" | "success" | "info" | "warning" | "muted";

const BAR: Record<MetricAccent, string> = {
  brand: "bg-brand",
  success: "bg-success",
  info: "bg-info",
  warning: "bg-warning",
  muted: "bg-border-strong",
};

const HINT: Record<MetricAccent, string> = {
  brand: "text-text-brand",
  success: "text-success",
  info: "text-info",
  warning: "text-warning",
  muted: "text-text-muted",
};

export function MetricCard({
  label,
  value,
  hint,
  accent = "brand",
  onClick,
}: {
  label: string;
  value: string;
  hint: string;
  accent?: MetricAccent;
  onClick?: () => void;
}) {
  const className = cn(
    "w-full overflow-hidden rounded-xl border border-border-default bg-surface p-4 text-left shadow-subtle",
    onClick && "cursor-pointer hover:border-border-brand",
  );

  const body = (
    <>
      <span className={cn("mb-3 block h-1 w-10 rounded-full", BAR[accent])} aria-hidden />
      <span className="block text-body-sm text-text-muted">{label}</span>
      <span className="mt-1 block text-[1.75rem] leading-tight font-bold tracking-[-0.02em] text-text-primary">
        {value}
      </span>
      <span className={cn("mt-2 block text-body-sm", HINT[accent])}>{hint}</span>
    </>
  );

  if (onClick) {
    return (
      <button type="button" className={className} onClick={onClick} aria-label={`${label}: ${value}`}>
        {body}
      </button>
    );
  }

  return <article className={className}>{body}</article>;
}
