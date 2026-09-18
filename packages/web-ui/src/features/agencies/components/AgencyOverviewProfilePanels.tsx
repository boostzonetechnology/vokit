import { FormEvent } from "react";

import { ActionButton } from "@/components/ui/ActionButton";
import { AgencyInfoTile } from "@/features/agencies/components/AgencyInfoTile";
import { AgencyStackField } from "@/features/agencies/components/AgencyStackField";
import { resolveCommissionDisplay } from "@/features/agencies/lib/commission";
import { formatAgencyStatus } from "@/features/agencies/lib/status";
import type { AgencyRecord } from "@/features/agencies/types";

export function AgencyOverviewPanel({ detail }: { detail: AgencyRecord }) {
  const commission = resolveCommissionDisplay(detail);
  const db = detail.database;

  return (
    <div className="grid w-full min-w-0 gap-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <AgencyInfoTile label="Agency status" value={formatAgencyStatus(detail.status)} />
        <AgencyInfoTile label="Tenant DB status" value={formatAgencyStatus(detail.tenant_status)} />
        <AgencyInfoTile label="Live commission" value={commission.liveLabel} />
        {commission.isScheduled ? (
          <AgencyInfoTile
            label="Scheduled commission"
            value={`${commission.scheduledLabel} · ${commission.effectiveAtLabel}`}
          />
        ) : (
          <AgencyInfoTile
            label="Rate effective"
            value={commission.effectiveAtLabel || "Immediate"}
          />
        )}
        <AgencyInfoTile label="Currency" value={detail.currency || "USD"} />
        <AgencyInfoTile label="Database" value={db?.name || "—"} />
        <AgencyInfoTile label="DB username" value={db?.username || "—"} />
        <AgencyInfoTile
          label="DB host"
          value={db ? `${db.host || "—"}:${db.port ?? "—"}` : "—"}
        />
        <AgencyInfoTile label="DB health" value={formatAgencyStatus(db?.status)} />
        <AgencyInfoTile label="Schema version" value={db?.schema_version || "—"} />
        <AgencyInfoTile
          label="TLS required"
          value={db?.tls_required == null ? "—" : db.tls_required ? "Yes" : "No"}
        />
      </div>
      <p className="m-0 text-body-sm text-text-muted">
        MySQL password is never returned by the API. Database name is server-allocated.
      </p>
    </div>
  );
}

export function AgencyProfilePanel({
  detail,
  busy,
  onSave,
}: {
  detail: AgencyRecord;
  busy: boolean;
  onSave: (input: { display_name: string; legal_name: string }) => Promise<void>;
}) {
  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await onSave({
      display_name: String(form.get("display_name") || ""),
      legal_name: String(form.get("legal_name") || ""),
    });
  }

  return (
    <form
      className="grid w-full min-w-0 gap-4 sm:grid-cols-2"
      onSubmit={(e) => void onSubmit(e)}
    >
      <AgencyStackField
        label="Display name"
        name="display_name"
        defaultValue={detail.display_name || ""}
        required
      />
      <AgencyStackField
        label="Legal name"
        name="legal_name"
        defaultValue={detail.legal_name || ""}
        required
      />
      <div className="sm:col-span-2">
        <ActionButton type="submit" disabled={busy}>
          Save profile
        </ActionButton>
      </div>
    </form>
  );
}
