import { Skeleton, SkeletonStatus } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";

/** Card/list row placeholder (agents, knowledge, integrations side lists). */
export function ListRowSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border-default bg-surface px-3 py-3",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1 space-y-2">
          <Skeleton className="h-4 w-40 max-w-full" />
          <Skeleton className="h-3 w-28 max-w-[80%]" />
        </div>
        <Skeleton className="h-5 w-16 shrink-0 rounded-full" />
      </div>
    </div>
  );
}

export function ListRowsSkeleton({
  rows = 6,
  className,
}: {
  rows?: number;
  className?: string;
}) {
  return (
    <div className={cn("grid gap-2", className)} role="status">
      <SkeletonStatus label="Loading list" />
      {Array.from({ length: rows }, (_, index) => (
        <ListRowSkeleton key={index} />
      ))}
    </div>
  );
}
