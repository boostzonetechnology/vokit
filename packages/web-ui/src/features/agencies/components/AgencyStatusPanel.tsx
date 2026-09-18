import { FormEvent, useMemo, useState } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import {
  AgencyStackSelect,
  AgencyStackTextarea,
} from "@/features/agencies/components/AgencyStackField";
import { formatAgencyStatus } from "@/features/agencies/lib/status";
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

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const confirm = form.get("confirm") === "on";
    if (!confirm) return;
    const reason = String(form.get("reason") || "").trim();
    if (needsReason && !reason) return;
    await onSave({ action, reason: reason || undefined });
  }

  return (
    <div className="grid w-full min-w-0 gap-5">
      <p className="m-0 text-body text-text-secondary">
        Current status:{" "}
        <strong className="text-text-primary">{formatAgencyStatus(detail.status)}</strong>
        {" · "}
        Tenant DB:{" "}
        <strong className="text-text-primary">
          {formatAgencyStatus(detail.tenant_status)}
        </strong>
      </p>

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
            I confirm this status change. Suspend turns new work off; existing customer services stay
            on unless changed under Capabilities.
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
