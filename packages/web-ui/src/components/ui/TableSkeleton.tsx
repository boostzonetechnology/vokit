import { Skeleton, SkeletonStatus } from "@/components/ui/Skeleton";

/** Table placeholder matching live `min-w-full` directory tables. */
export function TableSkeleton({
  columns = 5,
  rows = 6,
  headers,
}: {
  columns?: number;
  rows?: number;
  headers?: string[];
}) {
  const colCount = headers?.length ?? columns;

  return (
    <div className="overflow-auto" role="status">
      <SkeletonStatus label="Loading table" />
      <table className="min-w-full">
        {headers?.length ? (
          <thead>
            <tr className="text-label uppercase text-text-muted">
              {headers.map((header) => (
                <th key={header} className="border-0 px-2 py-2 text-left font-normal">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
        ) : (
          <thead>
            <tr>
              {Array.from({ length: colCount }, (_, index) => (
                <th key={index} className="border-0 px-2 py-2 text-left">
                  <Skeleton className="h-3 w-16" />
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {Array.from({ length: rows }, (_, rowIndex) => (
            <tr key={rowIndex} className="border-t border-border-default">
              {Array.from({ length: colCount }, (_, colIndex) => (
                <td key={colIndex} className="px-2 py-3">
                  <Skeleton
                    className={
                      colIndex === 0 ? "h-4 w-36 max-w-full" : "h-4 w-20 max-w-full"
                    }
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
