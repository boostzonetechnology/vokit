import {
  CAPABILITY_FIELDS,
  type AgencyCapabilities,
} from "@/features/agencies/types";

export type StatusActionImpact = {
  defaultsOff: string[];
  notifiesAgency: boolean;
  summary: string;
};

/** Server §24.1 defaults + VKT-034 notice behavior for status actions. */
export function statusActionImpact(action: string): StatusActionImpact {
  switch ((action || "").trim().toLowerCase()) {
    case "restrict":
      return {
        defaultsOff: ["Customer creation", "Payout requests"],
        notifiesAgency: true,
        summary:
          "Restrict turns new customer creation and payouts off. Agency members receive a mandatory suspension/restriction notice.",
      };
    case "review":
      return {
        defaultsOff: ["Payout requests"],
        notifiesAgency: false,
        summary:
          "Under review turns payout requests off. No agency notice is sent for this action.",
      };
    case "suspend":
      return {
        defaultsOff: [
          "Customer creation",
          "Agent creation",
          "Number purchase",
          "Payout requests",
        ],
        notifiesAgency: true,
        summary:
          "Suspend turns new commercial work off. Existing customer services stay on until you turn them off under Capabilities. Agency members are notified.",
      };
    case "close":
      return {
        defaultsOff: [],
        notifiesAgency: false,
        summary:
          "Close is final for status changes. Commercial actions stay blocked for everyone.",
      };
    case "activate":
    case "reactivate":
      return {
        defaultsOff: [],
        notifiesAgency: false,
        summary:
          "Sets the agency to Active. Capability flags are not auto-restored — review Capabilities after activate.",
      };
    default:
      return {
        defaultsOff: [],
        notifiesAgency: false,
        summary: "Confirm the action before applying.",
      };
  }
}

export function statusChangeSuccessMessage(action: string, nextStatus?: string): string {
  const impact = statusActionImpact(action);
  const label = (nextStatus || action).replaceAll("_", " ");
  if (impact.notifiesAgency) {
    return `Status updated to ${label}. Agency members were notified.`;
  }
  return `Status updated to ${label}.`;
}

export function disabledCapabilityLabels(
  capabilities?: AgencyCapabilities | null,
): string[] {
  if (!capabilities) return [];
  return CAPABILITY_FIELDS.filter((field) => !capabilities[field.key]).map(
    (field) => field.label,
  );
}

export function capabilityFormKey(capabilities?: AgencyCapabilities | null): string {
  if (!capabilities) return "none";
  return CAPABILITY_FIELDS.map(
    (field) => `${field.key}:${capabilities[field.key] ? "1" : "0"}`,
  ).join("|");
}

export function formatGateState(on: boolean): string {
  return on ? "Allowed" : "Blocked";
}
