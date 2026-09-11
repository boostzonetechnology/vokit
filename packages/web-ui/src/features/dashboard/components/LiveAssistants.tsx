import { cn } from "../../../lib/utils";
import type { PlatformAgentRow } from "../hooks/usePlatformDashboard";

function agentLabel(agent: PlatformAgentRow): string {
  return agent.display_name || agent.name || agent.id.slice(0, 8);
}

function statusTone(status?: string): { label: string; className: string } {
  const value = (status ?? "").toLowerCase();
  if (value === "active" || value === "live" || value === "published") {
    return { label: "Live", className: "text-success" };
  }
  if (value === "draft") {
    return { label: "Draft", className: "text-warning" };
  }
  if (value === "paused") {
    return { label: "Paused", className: "text-text-muted" };
  }
  return { label: status || "Unknown", className: "text-text-muted" };
}

export function LiveAssistants({
  agents,
  onNavigate,
}: {
  agents: PlatformAgentRow[];
  onNavigate: (href: string) => void;
}) {
  const rows = agents.slice(0, 5);

  return (
    <article className="flex h-full flex-col rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
      <h3 className="m-0 text-section text-text-primary">Live assistants</h3>
      <ul className="mt-4 m-0 flex-1 list-none space-y-3 p-0">
        {rows.length === 0 ? (
          <li className="text-body text-text-muted">No agents yet.</li>
        ) : (
          rows.map((agent) => {
            const tone = statusTone(agent.status);
            return (
              <li
                key={agent.id}
                className="flex items-center justify-between gap-3 border-b border-border-default pb-3 last:border-b-0 last:pb-0"
              >
                <div className="min-w-0">
                  <p className="m-0 truncate text-body font-semibold text-text-primary">
                    {agentLabel(agent)}
                  </p>
                  <p className="m-0 truncate text-body-sm text-text-muted">
                    {agent.customer_id ? `Customer ${agent.customer_id.slice(0, 8)}` : "Platform agent"}
                  </p>
                </div>
                <span className={cn("shrink-0 text-body-sm font-semibold", tone.className)}>
                  {tone.label}
                </span>
              </li>
            );
          })
        )}
      </ul>
      <button
        type="button"
        className="mt-4 bg-transparent p-0 text-body font-semibold text-text-brand"
        onClick={() => onNavigate("#/agents")}
      >
        Manage agents →
      </button>
    </article>
  );
}
