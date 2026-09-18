import { FormEvent } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { AgencyInfoTile } from "@/features/agencies/components/AgencyInfoTile";
import {
  AgencyStackField,
  AgencyStackTextarea,
} from "@/features/agencies/components/AgencyStackField";
import {
  datetimeLocalToIso,
  resolveCommissionDisplay,
} from "@/features/agencies/lib/commission";
import type { AgencyRecord, SetCommissionInput } from "@/features/agencies/types";

export function AgencyCommissionPanel({
  detail,
  busy,
  onSave,
}: {
  detail: AgencyRecord;
  busy: boolean;
  onSave: (input: SetCommissionInput) => Promise<void>;
}) {
  const commission = resolveCommissionDisplay(detail);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const reason = String(form.get("reason") || "").trim();
    if (!reason) return;
    const effectiveRaw = String(form.get("rate_effective_at") || "");
    await onSave({
      commission_rate_bps: Number(form.get("commission_rate_bps") || 0),
      reason,
      rate_effective_at: datetimeLocalToIso(effectiveRaw),
    });
  }

  return (
    <div className="grid w-full min-w-0 gap-5">
      <div className="grid gap-3 sm:grid-cols-2">
        <AgencyInfoTile label="Live rate" value={commission.liveLabel} />
        <AgencyInfoTile
          label={commission.isScheduled ? "Scheduled rate" : "Effective at"}
          value={
            commission.isScheduled
              ? `${commission.scheduledLabel} · ${commission.effectiveAtLabel}`
              : commission.effectiveAtLabel || "Live now"
          }
        />
      </div>

      <form
        className="grid w-full min-w-0 gap-4 sm:grid-cols-2"
        onSubmit={(e) => void onSubmit(e)}
      >
        <AgencyStackField
          label="New commission (bps)"
          name="commission_rate_bps"
          type="number"
          defaultValue={String(detail.commission_rate_bps ?? 1500)}
          required
        />
        <AgencyStackField
          label="Effective at (optional — leave empty for immediate)"
          name="rate_effective_at"
          type="datetime-local"
        />
        <AgencyStackTextarea
          className="sm:col-span-2"
          label="Reason (required)"
          name="reason"
          required
          rows={3}
          maxLength={500}
          placeholder="Why is this rate changing?"
        />
        <div className="sm:col-span-2">
          <ActionButton type="submit" disabled={busy}>
            Update commission
          </ActionButton>
        </div>
      </form>
      <p className="m-0 text-body-sm text-text-muted">
        Past effective dates are rejected. Historical ledger rows keep their original rate snapshot.
        Only one pending future change is kept.
      </p>
    </div>
  );
}
