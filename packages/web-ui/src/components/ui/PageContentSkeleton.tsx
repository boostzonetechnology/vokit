import { FormSectionSkeleton } from "@/components/ui/FormSectionSkeleton";
import { MetricGridSkeleton } from "@/components/ui/MetricCardSkeleton";
import { Skeleton, SkeletonStatus } from "@/components/ui/Skeleton";
import { TableSkeleton } from "@/components/ui/TableSkeleton";

/** Generic page body for Suspense / session bootstrap. */
export function PageContentSkeleton({
  showMetrics = false,
  showTable = true,
}: {
  showMetrics?: boolean;
  showTable?: boolean;
}) {
  return (
    <section className="mx-auto max-w-[1200px]" role="status">
      <SkeletonStatus label="Loading page" />
      <div className="mb-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="mt-2 h-4 w-80 max-w-full" />
      </div>
      {showMetrics ? <MetricGridSkeleton count={4} /> : null}
      {showTable ? (
        <article className="mt-6 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <div className="mb-4 flex items-center justify-between gap-3">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-10 w-40 rounded-xl" />
          </div>
          <TableSkeleton columns={5} rows={6} />
        </article>
      ) : (
        <article className="mt-6 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
          <FormSectionSkeleton fields={4} />
        </article>
      )}
    </section>
  );
}
