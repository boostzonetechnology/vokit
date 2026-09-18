import { AgencyInfoTile } from "@/features/agencies/components/AgencyInfoTile";
import { AgencyResourceTable } from "@/features/agencies/components/AgencyResourceTable";
import { formatCount } from "@/features/dashboard/lib/format";

function displayName(row: Record<string, unknown>): string {
  return String(
    row.display_name || row.name || row.email || row.title || row.e164 || "—",
  );
}

function withDisplayName(rows: Record<string, unknown>[]): Record<string, unknown>[] {
  return rows.map((row) => ({
    ...row,
    _name: displayName(row),
    _assigned: row.assigned_agent_id || row.agent_id ? "Assigned" : "Unassigned",
  }));
}

export function AgencyResourcesPanel({
  customers,
  agents,
  numbers,
  calls,
  integrations,
  team,
  knowledge,
}: {
  customers: Record<string, unknown>[];
  agents: Record<string, unknown>[];
  numbers: Record<string, unknown>[];
  calls: Record<string, unknown>[];
  integrations: Record<string, unknown>[];
  team: Record<string, unknown>[];
  knowledge: Record<string, unknown>[];
}) {
  const customerRows = withDisplayName(customers);
  const agentRows = withDisplayName(agents);
  const numberRows = withDisplayName(numbers);
  const teamRows = withDisplayName(team);
  const knowledgeRows = withDisplayName(knowledge);
  const integrationRows = withDisplayName(integrations);

  return (
    <div className="grid gap-5">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <AgencyInfoTile label="Customers" value={formatCount(customers.length)} />
        <AgencyInfoTile label="Agents" value={formatCount(agents.length)} />
        <AgencyInfoTile label="Numbers" value={formatCount(numbers.length)} />
        <AgencyInfoTile label="Calls" value={formatCount(calls.length)} />
        <AgencyInfoTile label="Team" value={formatCount(team.length)} />
        <AgencyInfoTile label="Knowledge" value={formatCount(knowledge.length)} />
        <AgencyInfoTile label="Connections" value={formatCount(integrations.length)} />
      </div>

      <AgencyResourceTable
        title="Customers"
        rows={customerRows}
        columns={[
          { key: "_name", label: "Name" },
          { key: "status", label: "Status", status: true },
        ]}
      />
      <AgencyResourceTable
        title="Agents"
        rows={agentRows}
        columns={[
          { key: "_name", label: "Name" },
          { key: "status", label: "Status", status: true },
          { key: "agent_type", label: "Type" },
        ]}
      />
      <AgencyResourceTable
        title="Numbers"
        rows={numberRows}
        columns={[
          { key: "e164", label: "Number" },
          { key: "status", label: "Status", status: true },
          { key: "_assigned", label: "Assignment" },
        ]}
      />
      <AgencyResourceTable
        title="Team"
        rows={teamRows}
        columns={[
          { key: "_name", label: "Member" },
          { key: "role", label: "Role" },
          { key: "status", label: "Status", status: true },
        ]}
      />
      <AgencyResourceTable
        title="Knowledge"
        rows={knowledgeRows}
        columns={[
          { key: "_name", label: "Item" },
          { key: "status", label: "Status", status: true },
        ]}
      />
      <AgencyResourceTable
        title="Connections"
        rows={integrationRows}
        columns={[
          { key: "_name", label: "Connection" },
          { key: "status", label: "Status", status: true },
        ]}
      />
      <AgencyResourceTable
        title="Calls"
        rows={calls}
        columns={[
          { key: "direction", label: "Direction" },
          { key: "status", label: "Status", status: true },
          { key: "started_at", label: "Started" },
        ]}
      />
    </div>
  );
}
