import type { AgencyRecord } from "@/features/agencies/types";
import { bpsToPercent } from "@/features/agencies/lib/status";

export type CommissionDisplay = {
  liveBps: number | undefined;
  liveLabel: string;
  scheduledBps: number | undefined;
  scheduledLabel: string | null;
  effectiveAtLabel: string | null;
  isScheduled: boolean;
};

/** Live vs scheduled commission per ADR-010 / agency finance contract. */
export function resolveCommissionDisplay(
  agency: Pick<
    AgencyRecord,
    "commission_rate_bps" | "previous_commission_rate_bps" | "rate_effective_at"
  >,
  now = new Date(),
): CommissionDisplay {
  const effectiveAt = agency.rate_effective_at ? new Date(agency.rate_effective_at) : null;
  const isScheduled = Boolean(effectiveAt && effectiveAt.getTime() > now.getTime());

  if (isScheduled) {
    return {
      liveBps: agency.previous_commission_rate_bps,
      liveLabel: bpsToPercent(agency.previous_commission_rate_bps),
      scheduledBps: agency.commission_rate_bps,
      scheduledLabel: bpsToPercent(agency.commission_rate_bps),
      effectiveAtLabel: effectiveAt ? effectiveAt.toLocaleString() : null,
      isScheduled: true,
    };
  }

  return {
    liveBps: agency.commission_rate_bps,
    liveLabel: bpsToPercent(agency.commission_rate_bps),
    scheduledBps: undefined,
    scheduledLabel: null,
    effectiveAtLabel: effectiveAt ? effectiveAt.toLocaleString() : null,
    isScheduled: false,
  };
}

/** Convert datetime-local value to ISO UTC for API. */
export function datetimeLocalToIso(value: string): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = new Date(trimmed);
  if (Number.isNaN(parsed.getTime())) return undefined;
  return parsed.toISOString();
}
