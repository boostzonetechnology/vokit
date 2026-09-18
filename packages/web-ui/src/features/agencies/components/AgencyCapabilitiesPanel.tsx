import { FormEvent } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AgencyStackTextarea } from "@/features/agencies/components/AgencyStackField";
import { capabilityFormKey } from "@/features/agencies/lib/gates";
import {
  agencyStatusTone,
  formatAgencyStatus,
} from "@/features/agencies/lib/status";
import {
  CAPABILITY_FIELDS,
  defaultCapabilities,
  type AgencyCapabilities,
  type AgencyRecord,
} from "@/features/agencies/types";

export function AgencyCapabilitiesPanel({
  detail,
  busy,
  onSave,
}: {
  detail: AgencyRecord;
  busy: boolean;
  onSave: (input: { capabilities: AgencyCapabilities; reason: string }) => Promise<void>;
}) {
  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail.capabilities) return;
    const form = new FormData(event.currentTarget);
    if (form.get("confirm") !== "on") return;
    const reason = String(form.get("reason") || "").trim();
    if (!reason) return;
    const next = { ...defaultCapabilities() };
    for (const field of CAPABILITY_FIELDS) {
      next[field.key] = form.get(field.key) === "on";
    }
    await onSave({ capabilities: next, reason });
  }

  return (
    <div className="grid w-full min-w-0 gap-5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-body text-text-secondary">Current agency status</span>
        <StatusBadge tone={agencyStatusTone(detail.status)}>
          {formatAgencyStatus(detail.status)}
        </StatusBadge>
      </div>

      <form
        key={capabilityFormKey(detail.capabilities)}
        className="grid w-full min-w-0 gap-4"
        onSubmit={(e) => void onSubmit(e)}
      >
        <div className="grid gap-2 sm:grid-cols-2">
          {CAPABILITY_FIELDS.map((field) => (
            <label
              key={field.key}
              className="m-0 flex min-w-0 items-start gap-2.5 rounded-xl border border-border-default bg-canvas px-3 py-3 font-normal"
            >
              <input
                type="checkbox"
                name={field.key}
                defaultChecked={Boolean(detail.capabilities?.[field.key])}
                className="mt-1 shrink-0"
              />
              <span className="min-w-0">
                <span className="block text-body font-medium text-text-primary">
                  {field.label}
                </span>
                <span className="mt-0.5 block text-body-sm text-text-muted">{field.hint}</span>
              </span>
            </label>
          ))}
        </div>

        <p className="m-0 text-body-sm text-text-muted" role="note">
          Capability changes do not send a notification. Restrict/suspend notices come from the
          Status tab. Turning off existing customer services blocks new production admission only.
        </p>

        <AgencyStackTextarea
          label="Reason (required)"
          name="reason"
          required
          rows={3}
          placeholder="Why are these capability gates changing?"
        />

        <label className="m-0 flex w-full min-w-0 items-start gap-2.5 font-normal">
          <input type="checkbox" name="confirm" required className="mt-1 shrink-0" />
          <span className="text-body text-text-secondary">
            I confirm these capability changes. Gates are enforced on every protected API.
          </span>
        </label>

        <div>
          <ActionButton type="submit" disabled={busy || !detail.capabilities}>
            Save capabilities
          </ActionButton>
        </div>
      </form>
    </div>
  );
}
