import type { BadgeTone } from "@/components/ui/StatusBadge";
import {
  WEEKDAY_LABELS,
  type BusinessHoursWindow,
  type CustomerAgentDetail,
} from "@/features/agents/types";

export function agentStatusTone(status?: string): BadgeTone {
  const value = (status ?? "").toLowerCase();
  if (value === "active") return "success";
  if (value === "paused" || value === "draft" || value === "testing") return "warning";
  if (value === "suspended" || value === "error" || value === "archived") return "danger";
  return "neutral";
}

export function canCustomerPause(detail: CustomerAgentDetail | null | undefined): boolean {
  if (!detail?.customer_can_edit || detail.status_locked) return false;
  const status = (detail.status ?? "").toLowerCase();
  return status === "active" || status === "testing";
}

export function canCustomerResume(detail: CustomerAgentDetail | null | undefined): boolean {
  if (!detail?.customer_can_edit || detail.status_locked) return false;
  return (detail.status ?? "").toLowerCase() === "paused";
}

export function formatBoolOnOff(value?: boolean): string {
  if (value === true) return "On";
  if (value === false) return "Off";
  return "—";
}

export function formatOptional(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

export function formatBusinessHours(
  windows: BusinessHoursWindow[] | undefined,
): string {
  if (!windows?.length) return "Always open";
  return windows
    .map((row) => {
      const day = WEEKDAY_LABELS[row.weekday] ?? `Day ${row.weekday}`;
      return `${day.slice(0, 3)} ${row.start}–${row.end}`;
    })
    .join(", ");
}

export function formatTools(tools: string[] | undefined): string {
  if (!tools?.length) return "None";
  return tools.join(", ");
}
