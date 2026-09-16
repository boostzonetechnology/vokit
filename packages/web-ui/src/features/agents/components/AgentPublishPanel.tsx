import { useNavigate } from "react-router-dom";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormSelect } from "@/components/forms/FormSelect";
import { StatusBadge, type BadgeTone } from "@/components/ui/StatusBadge";
import type { AgentRoutingResult, CustomerOption, PlatformAgentDetail } from "@/features/agents/types";
import { toAppPath } from "@/nav";

function statusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "paused" || value === "draft" || value === "testing") return "warning";
  if (value === "suspended" || value === "error" || value === "archived") return "danger";
  return "neutral";
}

export function AgentPublishPanel({
  detail,
  busy,
  routing,
  routingLoading,
  customers,
  cloneCustomerId,
  onCloneCustomerChange,
  onRefreshRouting,
  onPublish,
  onPause,
  onClone,
  showNumbersLink = true,
}: {
  detail: PlatformAgentDetail;
  busy: boolean;
  routing: AgentRoutingResult | null;
  routingLoading?: boolean;
  customers: CustomerOption[];
  cloneCustomerId: string;
  onCloneCustomerChange: (customerId: string) => void;
  onRefreshRouting: () => void;
  onPublish: () => void;
  onPause: () => void;
  onClone: () => void;
  showNumbersLink?: boolean;
}) {
  const navigate = useNavigate();
  const locked = Boolean(detail.status_locked);

  return (
    <div className="grid gap-4">
      <div className="grid gap-2 sm:grid-cols-2">
        <div className="rounded-lg border border-border-default px-3 py-2">
          <p className="m-0 text-body-sm text-text-muted">Status</p>
          <StatusBadge tone={statusTone(detail.status)}>{detail.status || "—"}</StatusBadge>
        </div>
        <div className="rounded-lg border border-border-default px-3 py-2">
          <p className="m-0 text-body-sm text-text-muted">Versions</p>
          <p className="m-0 text-body text-text-primary">
            draft {detail.draft_version ?? "—"} · published {detail.published_version ?? "—"}
          </p>
        </div>
        <div className="rounded-lg border border-border-default px-3 py-2">
          <p className="m-0 text-body-sm text-text-muted">Production routable</p>
          <p className="m-0 text-body text-text-primary">
            {detail.production_routable ? "Yes" : "No"}
          </p>
        </div>
        <div className="rounded-lg border border-border-default px-3 py-2">
          <p className="m-0 text-body-sm text-text-muted">Status lock</p>
          <p className="m-0 text-body text-text-primary">
            {locked ? `Yes (${detail.status_actor || "—"})` : "No"}
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-border-default bg-canvas px-3 py-3">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <p className="m-0 text-body-sm font-semibold text-text-primary">Routing check</p>
          <ActionButton
            type="button"
            variant="outline"
            disabled={busy || routingLoading}
            onClick={onRefreshRouting}
          >
            {routingLoading ? "Checking…" : "Refresh routing"}
          </ActionButton>
        </div>
        {routing ? (
          <p className="m-0 text-body text-text-secondary" role="status">
            {routing.routable
              ? "Routable for production inbound."
              : `Not routable${routing.reason ? `: ${routing.reason}` : "."}`}
          </p>
        ) : (
          <p className="m-0 text-sm text-text-muted">
            Run routing check before publish to see subscription / voice / number gates.
          </p>
        )}
      </div>

      <p className="m-0 text-body text-text-secondary">
        Publish is subject to customer plan, balance, and status on the server (AG3-004).
        {locked
          ? " Platform has locked status — pause/publish may be blocked for agency."
          : ""}
      </p>

      <div className="flex flex-wrap gap-2">
        <ActionButton disabled={busy || locked} onClick={onPublish}>
          Publish / activate
        </ActionButton>
        <ActionButton variant="outline" disabled={busy || locked} onClick={onPause}>
          Pause / deactivate
        </ActionButton>
        {showNumbersLink ? (
          <ActionButton
            variant="secondary"
            onClick={() => navigate(toAppPath("/numbers"))}
          >
            Assign number…
          </ActionButton>
        ) : null}
      </div>

      <div className="grid gap-3 rounded-xl border border-border-default px-3 py-3">
        <p className="m-0 text-body-sm font-semibold text-text-primary">Clone (ADR-009)</p>
        <p className="m-0 text-sm text-text-muted">
          Optional target customer in the same agency. Leave blank to clone onto the same
          customer.
        </p>
        <FormSelect
          label="Target customer"
          name="clone_customer"
          value={cloneCustomerId}
          onChange={(event) => onCloneCustomerChange(event.target.value)}
        >
          <option value="">Same customer</option>
          {customers.map((row) => (
            <option key={row.id} value={row.id}>
              {row.display_name || row.id.slice(0, 8)}
            </option>
          ))}
        </FormSelect>
        <ActionButton variant="secondary" disabled={busy} onClick={onClone}>
          Clone agent
        </ActionButton>
      </div>
    </div>
  );
}
