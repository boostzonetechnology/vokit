import { cn } from "@/lib/utils";
import type { PlatformAgentRow, PlatformCallRow } from "@/features/dashboard/hooks/usePlatformDashboard";
import { formatDuration, formatRelativeTime } from "@/features/dashboard/lib/format";

function outcome(status?: string): { label: string; className: string } {
  const value = (status ?? "").toLowerCase();
  if (value === "completed" || value === "ended") {
    return { label: "Resolved", className: "bg-info/10 text-info" };
  }
  if (value === "transferred") {
    return { label: "Transferred", className: "bg-warning/10 text-warning" };
  }
  if (value === "failed" || value === "no_answer" || value === "busy") {
    return { label: "Missed", className: "bg-danger/10 text-danger" };
  }
  if (value === "answered" || value === "in_progress" || value === "ringing") {
    return { label: "Booked", className: "bg-success/10 text-success" };
  }
  return { label: status || "Unknown", className: "bg-canvas text-text-muted" };
}

function agentName(call: PlatformCallRow, agents: PlatformAgentRow[]): string {
  const match = agents.find((agent) => agent.id === call.agent_id);
  if (match?.display_name || match?.name) {
    return match.display_name || match.name || "Agent";
  }
  return call.agent_id ? call.agent_id.slice(0, 8) : "—";
}

export function RecentCallsTable({
  calls,
  agents,
  onNavigate,
}: {
  calls: PlatformCallRow[];
  agents: PlatformAgentRow[];
  onNavigate: (href: string) => void;
}) {
  const rows = calls.slice(0, 6);

  return (
    <article className="rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="m-0 text-section text-text-primary">Recent calls</h3>
        <button
          type="button"
          className="bg-transparent p-0 text-body font-semibold text-text-brand"
          onClick={() => onNavigate("#/calls")}
        >
          View call log →
        </button>
      </div>

      {rows.length === 0 ? (
        <p className="m-0 py-10 text-center text-body text-text-muted">No recent calls.</p>
      ) : (
        <div className="overflow-auto">
          <table className="min-w-full">
            <caption className="sr-only">Recent calls</caption>
            <thead>
              <tr className="text-label uppercase text-text-muted">
                <th className="border-0 px-2 py-2">Caller</th>
                <th className="border-0 px-2 py-2">Agent</th>
                <th className="border-0 px-2 py-2">Duration</th>
                <th className="border-0 px-2 py-2">Outcome</th>
                <th className="border-0 px-2 py-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((call) => {
                const tone = outcome(call.status);
                return (
                  <tr
                    key={call.id}
                    className="cursor-pointer hover:bg-brand-subtle/40"
                    onClick={() => onNavigate("#/calls")}
                  >
                    <td className="px-2 py-3 font-medium text-text-primary">
                      {call.remote_e164 || call.e164 || call.id.slice(0, 8)}
                    </td>
                    <td className="px-2 py-3 text-text-secondary">{agentName(call, agents)}</td>
                    <td className="px-2 py-3 text-text-secondary">
                      {formatDuration(call.duration_seconds, call.billed_minutes)}
                    </td>
                    <td className="px-2 py-3">
                      <span
                        className={cn(
                          "inline-flex rounded-full px-2.5 py-0.5 text-body-sm font-semibold",
                          tone.className,
                        )}
                      >
                        {tone.label}
                      </span>
                    </td>
                    <td className="px-2 py-3 text-text-muted">
                      {formatRelativeTime(call.started_at ?? call.ended_at)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}
