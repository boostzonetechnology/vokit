import { Skeleton, SkeletonStatus } from "@/components/ui/Skeleton";

/** Matches DualLineChart article + svg height (~200px plot). */
export function ChartSkeleton({ titleWidth = "w-40" }: { titleWidth?: string }) {
  return (
    <article
      className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle"
      role="status"
    >
      <SkeletonStatus label="Loading chart" />
      <div className="mb-4 flex items-center justify-between gap-3">
        <Skeleton className={`h-5 ${titleWidth}`} />
        <Skeleton className="h-7 w-14 rounded-md" />
      </div>
      <Skeleton className="h-[200px] w-full rounded-lg" />
      <div className="mt-3 flex justify-between gap-2">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-16" />
      </div>
    </article>
  );
}
