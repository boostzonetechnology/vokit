import { ChartSkeleton } from "@/components/ui/ChartSkeleton";
import { MetricGridSkeleton } from "@/components/ui/MetricCardSkeleton";
import { Skeleton, SkeletonStatus } from "@/components/ui/Skeleton";
import { TableSkeleton } from "@/components/ui/TableSkeleton";

/** Shared dashboard body placeholder — KPI grid + chart + side table. */
export function DashboardBodySkeleton({
  metricCount = 8,
  metricGridClassName = "grid gap-4 sm:grid-cols-2 xl:grid-cols-4",
}: {
  metricCount?: number;
  metricGridClassName?: string;
}) {
  return (
    <div className="grid gap-4" role="status">
      <SkeletonStatus label="Loading dashboard" />
      <MetricGridSkeleton count={metricCount} className={metricGridClassName} />
      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <ChartSkeleton />
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 flex items-center justify-between gap-3">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-4 w-16" />
          </div>
          <TableSkeleton columns={3} rows={5} />
        </article>
      </div>
      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4">
            <Skeleton className="h-5 w-36" />
          </div>
          <TableSkeleton columns={4} rows={5} />
        </article>
        <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4">
            <Skeleton className="h-5 w-28" />
          </div>
          <div className="grid gap-3">
            {Array.from({ length: 4 }, (_, index) => (
              <div key={index} className="flex items-center justify-between gap-3">
                <div className="min-w-0 flex-1 space-y-2">
                  <Skeleton className="h-4 w-40 max-w-full" />
                  <Skeleton className="h-3 w-24" />
                </div>
                <Skeleton className="h-5 w-14 rounded-full" />
              </div>
            ))}
          </div>
        </article>
      </div>
    </div>
  );
}
