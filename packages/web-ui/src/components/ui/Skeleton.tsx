import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

/** Base pulse block for layout-matched loading placeholders. */
export function Skeleton({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-border-default/70", className)}
      aria-hidden
      {...props}
    />
  );
}

export function SkeletonStatus({ label = "Loading" }: { label?: string }) {
  return <span className="sr-only">{label}</span>;
}
