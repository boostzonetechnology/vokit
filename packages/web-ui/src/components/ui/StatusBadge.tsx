import { cn } from "@/lib/utils";

export type BadgeTone = "success" | "warning" | "danger" | "info" | "neutral";

const TONE: Record<BadgeTone, string> = {
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  danger: "bg-danger/10 text-danger",
  info: "bg-info/10 text-info",
  neutral: "bg-canvas text-text-muted",
};

export function StatusBadge({
  children,
  tone = "neutral",
}: {
  children: string;
  tone?: BadgeTone;
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-0.5 text-body-sm font-semibold",
        TONE[tone],
      )}
    >
      {children}
    </span>
  );
}
