import { FormEvent, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  AgencyStackSelect,
  AgencyStackTextarea,
} from "@/features/agencies/components/AgencyStackField";
import { statusActionImpact } from "@/features/agencies/lib/gates";
import {
  agencyStatusTone,
  formatAgencyStatus,
} from "@/features/agencies/lib/status";
import {
  STATUS_ACTIONS,
  statusActionNeedsReason,
  type AgencyRecord,
} from "@/features/agencies/types";

export function AgencyStatusPanel({
  detail,
  busy,
  onSave,
}: {
  detail: AgencyRecord;
  busy: boolean;
  onSave: (input: { action: string; reason?: string }) => Promise<void>;
}) {
  const [action, setAction] = useState<string>(STATUS_ACTIONS[0].action);
  const needsReason = useMemo(() => statusActionNeedsReason(action), [action]);
  const impact = useMemo(() => statusActionImpact(action), [action]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    if (form.get("confirm") !== "on") return;
    const reason = String(form.get("reason") || "").trim();
    if (needsReason && !reason) return;
    await onSave({ action, reason: reason || undefined });
  }

  return (
    <div className="grid w-full min-w-0 gap-5">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="min-w-0 rounded-xl border border-border-default bg-canvas px-3.5 py-3.5">
          <p className="m-0 text-body-sm text-text-muted">Agency status</p>
          <div className="mt-2">
            <StatusBadge tone={agencyStatusTone(detail.status)}>
              {formatAgencyStatus(detail.status)}
            </StatusBadge>
          </div>
        </div>
        <div className="min-w-0 rounded-xl border border-border-default bg-canvas px-3.5 py-3.5">
          <p className="m-0 text-body-sm text-text-muted">Tenant DB</p>
          <div className="mt-2">
            <StatusBadge tone={agencyStatusTone(detail.tenant_status)}>
              {formatAgencyStatus(detail.tenant_status)}
            </StatusBadge>
          </div>
        </div>
      </div>

      <form className="grid w-full min-w-0 gap-4" onSubmit={(e) => void onSubmit(e)}>
        <AgencyStackSelect
          label="Status action"
          value={action}
          onChange={(event) => setAction(event.target.value)}
        >
          {STATUS_ACTIONS.map((item) => (
            <option key={item.action} value={item.action}>
              {item.label}
            </option>
          ))}
        </AgencyStackSelect>

        <div
          className="rounded-xl border border-border-default bg-canvas px-3.5 py-3.5"
          role="note"
        >
          <p className="m-0 text-body text-text-secondary">{impact.summary}</p>
          {impact.defaultsOff.length > 0 ? (
            <p className="mt-2 mb-0 text-body-sm text-text-muted">
              Defaults forced off: {impact.defaultsOff.join(" · ")}
            </p>
          ) : null}
          <p className="mt-2 mb-0 text-body-sm text-text-muted">
            {impact.notifiesAgency
              ? "Notification: agency members receive agency.suspended (mandatory)."
              : "Notification: none for this action."}
          </p>
        </div>

        {needsReason ? (
          <AgencyStackTextarea
            label="Reason (required)"
            name="reason"
            required
            rows={3}
            placeholder="Required for restrict, review, suspend, and close"
          />
        ) : null}

        <label className="m-0 flex w-full min-w-0 items-start gap-2.5 font-normal">
          <input type="checkbox" name="confirm" required className="mt-1 shrink-0" />
          <span className="text-body text-text-secondary">
            I confirm this status change. Server gates apply immediately; the UI cannot bypass them.
          </span>
        </label>

        <div>
          <ActionButton type="submit" disabled={busy}>
            Apply status
          </ActionButton>
        </div>
      </form>
    </div>
  );
}
