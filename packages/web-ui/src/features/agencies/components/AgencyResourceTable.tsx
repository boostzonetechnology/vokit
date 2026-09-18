import { StatusBadge } from "@/components/ui/StatusBadge";
import { agencyStatusTone } from "@/features/agencies/lib/status";

export function AgencyResourceTable({
  title,
  rows,
  columns,
}: {
  title: string;
  rows: Record<string, unknown>[];
  columns: Array<{ key: string; label: string; status?: boolean }>;
}) {
  return (
    <div>
      <h3 className="m-0 mb-2 text-section text-text-primary">
        {title}
        <span className="ml-2 text-body font-normal text-text-muted">({rows.length})</span>
      </h3>
      {rows.length === 0 ? (
        <p className="m-0 text-body text-text-muted">No {title.toLowerCase()} for this agency.</p>
      ) : (
        <div className="overflow-auto rounded-xl border border-border-default">
          <table className="min-w-full">
            <thead>
              <tr className="bg-canvas text-label uppercase text-text-muted">
                {columns.map((col) => (
                  <th key={col.key} className="border-0 px-3 py-2.5 text-left">
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 12).map((row, index) => (
                <tr key={String(row.id ?? `${title}-${index}`)} className="border-t border-border-default">
                  {columns.map((col) => (
                    <td key={col.key} className="px-3 py-3 text-text-secondary">
                      {col.status ? (
                        <StatusBadge tone={agencyStatusTone(String(row[col.key] ?? ""))}>
                          {String(row[col.key] ?? "—").replaceAll("_", " ")}
                        </StatusBadge>
                      ) : (
                        String(row[col.key] ?? "—")
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
