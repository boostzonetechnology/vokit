import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { CustomerAgentDetailPanel } from "@/features/agents/components/CustomerAgentDetailPanel";
import { CustomerAgentListPanel } from "@/features/agents/components/CustomerAgentListPanel";
import { useCustomerAgents } from "./hooks/useCustomerAgents";

export function CustomerAgentsScreen() {
  const {
    agents,
    detail,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    detailLoading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    statusOptions,
    reload,
    saveLimitedFields,
    pauseAgent,
    resumeAgent,
  } = useCustomerAgents();

  return (
    <section className="mx-auto max-w-[1200px]">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
            Agents
          </h1>
          <p className="mt-1 mb-0 text-body text-text-muted">
            Monitor assigned agents, number, and configuration · CU2-001–003
          </p>
        </div>
        <ActionButton variant="secondary" onClick={() => void reload()}>
          Refresh
        </ActionButton>
      </div>

      {error ? (
        <p className="mb-4 text-danger" role="alert">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="mb-4 text-body text-text-brand" role="status">
          {message}
        </p>
      ) : null}

      <div className="mb-4 grid gap-3 sm:grid-cols-2">
        <FormField
          label="Search"
          name="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Name, number, status…"
        />
        <FormSelect
          label="Status"
          name="status"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="">All statuses</option>
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </FormSelect>
      </div>

      <div className="grid min-w-0 gap-4 lg:grid-cols-[1.05fr_1.15fr]">
        <CustomerAgentListPanel
          agents={agents}
          selectedId={selectedId}
          loading={loading}
          onSelect={setSelectedId}
        />
        <CustomerAgentDetailPanel
          detail={detail}
          detailLoading={detailLoading}
          busy={busy}
          onPause={async () => {
            await pauseAgent();
          }}
          onResume={async () => {
            await resumeAgent();
          }}
          onSaveLimitedFields={saveLimitedFields}
        />
      </div>
    </section>
  );
}
