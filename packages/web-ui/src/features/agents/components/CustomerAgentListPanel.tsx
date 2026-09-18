import { ListRowsSkeleton } from "@/components/ui/ListRowSkeleton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { agentStatusTone } from "@/features/agents/lib/customerAgentStatus";
import type { CustomerAgentRow } from "@/features/agents/types";

export function CustomerAgentListPanel({
  agents,
  selectedId,
  loading,
  onSelect,
}: {
  agents: CustomerAgentRow[];
  selectedId: string;
  loading: boolean;
  onSelect: (agentId: string) => void;
}) {
  return (
    <article className="min-w-0 rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
      <h2 className="m-0 mb-3 text-section text-text-primary">
        Assigned agents
        <span className="ml-2 text-body font-normal text-text-muted">({agents.length})</span>
      </h2>

      {loading && agents.length === 0 ? (
        <ListRowsSkeleton rows={8} />
      ) : !agents.length ? (
        <p className="m-0 py-10 text-center text-body text-text-muted">
          No agents assigned to this customer yet.
        </p>
      ) : (
        <ul className="m-0 grid max-h-[640px] list-none gap-2 overflow-auto p-0">
          {agents.map((row) => {
            const selected = row.id === selectedId;
            return (
              <li key={row.id}>
                <button
                  type="button"
                  className={
                    selected
                      ? "flex w-full items-start justify-between gap-3 rounded-xl border border-brand bg-canvas px-3 py-3 text-left"
                      : "flex w-full items-start justify-between gap-3 rounded-xl border border-border-default bg-surface px-3 py-3 text-left hover:bg-canvas"
                  }
                  onClick={() => onSelect(row.id)}
                >
                  <div className="min-w-0">
                    <p className="m-0 truncate font-semibold text-text-primary">
                      {row.display_name || row.id.slice(0, 8)}
                    </p>
                    <p className="m-0 mt-1 text-body-sm text-text-muted">
                      {row.assigned_e164 || "No number"}
                      {row.agent_type ? ` · ${row.agent_type}` : ""}
                    </p>
                    {row.production_routable != null ? (
                      <p className="m-0 mt-0.5 text-xs text-text-secondary">
                        {row.production_routable ? "Production routable" : "Not production routable"}
                      </p>
                    ) : null}
                  </div>
                  <StatusBadge tone={agentStatusTone(row.status)}>
                    {row.status || "—"}
                  </StatusBadge>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </article>
  );
}
