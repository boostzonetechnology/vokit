import type { BadgeTone } from "@/components/ui/StatusBadge";

/** Platform delivery/inbox labels for KYC + suspension (VKT-034) and related events. */
export function notificationEventKind(eventType?: string): {
  label: string;
  tone: BadgeTone;
} {
  const value = (eventType || "").toLowerCase();
  if (value.startsWith("kyc.")) {
    return { label: "KYC", tone: "warning" };
  }
  if (value === "agency.suspended") {
    return { label: "Suspension", tone: "danger" };
  }
  if (value.startsWith("invitation.")) {
    return { label: "Invite", tone: "info" };
  }
  if (
    value.startsWith("payout.") ||
    value.startsWith("payment.") ||
    value === "commission.available" ||
    value === "minutes.low"
  ) {
    return { label: "Billing", tone: "success" };
  }
  if (value.startsWith("announcement.")) {
    return { label: "Announcement", tone: "neutral" };
  }
  if (value.startsWith("security.")) {
    return { label: "Security", tone: "danger" };
  }
  return { label: "Event", tone: "neutral" };
}

export function notificationCategoryTone(category?: string): BadgeTone {
  switch ((category || "").toLowerCase()) {
    case "kyc":
      return "warning";
    case "suspension":
      return "danger";
    case "billing":
      return "success";
    case "security":
      return "danger";
    case "invitation":
      return "info";
    default:
      return "neutral";
  }
}
