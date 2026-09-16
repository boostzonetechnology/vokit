import { Skeleton, SkeletonStatus } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";

/** Settings / MFA / detail form field placeholders. */
export function FormSectionSkeleton({
  fields = 4,
  className,
}: {
  fields?: number;
  className?: string;
}) {
  return (
    <div className={cn("grid gap-4", className)} role="status">
      <SkeletonStatus label="Loading form" />
      {Array.from({ length: fields }, (_, index) => (
        <div key={index} className="grid gap-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-11 w-full rounded-xl" />
        </div>
      ))}
    </div>
  );
}
