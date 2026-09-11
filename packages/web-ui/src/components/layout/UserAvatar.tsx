import type { SessionPayload } from "@/api";
import { cn } from "@/lib/utils";

function initials(email: string): string {
  const local = email.split("@")[0] ?? "U";
  const parts = local.split(/[._-]/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0]![0] ?? ""}${parts[1]![0] ?? ""}`.toUpperCase();
  }
  return local.slice(0, 2).toUpperCase();
}

export function UserAvatar({
  session,
  size = "md",
}: {
  session: SessionPayload;
  size?: "sm" | "md";
}) {
  const sizeClass = size === "sm" ? "size-10 text-body-sm" : "size-10 text-body";
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full bg-violet-100 font-semibold text-text-brand",
        sizeClass,
      )}
      aria-hidden
    >
      {initials(session.user.email)}
    </span>
  );
}
