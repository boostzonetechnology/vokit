import { Skeleton, SkeletonStatus } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";

/** Mirrors MetricCard chrome so KPI grids do not jump when data arrives. */
export function MetricCardSkeleton({ className }: { className?: string }) {
  return (
    <article
      className={cn(
        "w-full overflow-hidden rounded-xl border border-border-default bg-surface p-4 shadow-subtle",
        className,
      )}
      role="status"
    >
      <SkeletonStatus label="Loading metric" />
      <Skeleton className="mb-3 h-1 w-10 rounded-full" />
      <Skeleton className="h-4 w-24" />
      <Skeleton className="mt-2 h-8 w-28" />
      <Skeleton className="mt-3 h-4 w-36" />
    </article>
  );
}

export function MetricGridSkeleton({
  count = 4,
  className = "grid gap-4 sm:grid-cols-2 xl:grid-cols-4",
}: {
  count?: number;
  className?: string;
}) {
  return (
    <div className={className} role="status">
      <SkeletonStatus label="Loading metrics" />
      {Array.from({ length: count }, (_, index) => (
        <MetricCardSkeleton key={index} />
      ))}
    </div>
  );
}
