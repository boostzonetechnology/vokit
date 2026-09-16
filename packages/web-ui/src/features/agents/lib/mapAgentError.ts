import { isApiError } from "@/api";

/** Map DomainError codes from agent configure/publish/clone/knowledge. */
export function mapAgentError(cause: unknown, fallback: string): string {
  if (!isApiError(cause)) {
    return fallback;
  }
  switch (cause.code) {
    case "subscription_required":
      return (
        cause.message ||
        "Customer needs an active plan subscription before this agent can be published."
      );
    case "customer_inactive":
      return cause.message || "Customer must be Active before publishing this agent.";
    case "customer_risk_blocked":
      return cause.message || "Customer is risk-blocked. Clear the risk case first.";
    case "instructions_required":
      return cause.message || "Add agent instructions before publishing.";
    case "voice_required":
      return cause.message || "Select a voice before publishing.";
    case "compliance_required":
      return (
        cause.message ||
        "Enable recording disclosure (compliance) before publishing."
      );
    case "fallback_required":
      return cause.message || "Set a fallback behavior before publishing.";
    case "agent_suspended":
      return cause.message || "Agent is suspended and cannot be published.";
    case "agent_archived":
      return cause.message || "Restore the archived agent before editing or publishing.";
    case "status_locked":
      return (
        cause.message ||
        "Platform has locked this agent's status. Agency cannot change it."
      );
    case "validation_error":
      return cause.message || fallback;
    case "forbidden":
    case "permission_denied":
      return cause.message || "You do not have permission for this agent action.";
    default:
      return cause.message || fallback;
  }
}
