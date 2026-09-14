import type { Portal } from "@/api";

/**
 * High-risk routes only (P5). Returns permission codes — user needs any one (canAny).
 * null = not gated in V1.
 */
export function highRiskPermissionsForRoute(
  portal: Portal,
  route: string,
): string[] | null {
  const base = route.split("/")[0] ?? route;

  if (portal === "platform") {
    switch (base) {
      case "users":
        return ["user.view", "user.create"];
      case "roles":
        return ["role.view"];
      case "permissions":
        return ["permission.view"];
      case "kyc":
        return ["kyc.review"];
      case "payouts":
        return ["payout.approve"];
      case "settings":
        return ["setting.view"];
      default:
        return null;
    }
  }

  if (portal === "agency") {
    switch (base) {
      case "wallet":
        return ["wallet.view"];
      case "payouts":
        return ["payout.request", "wallet.view"];
      case "settings":
      case "preferences":
        return ["notice.view", "notice.update"];
      default:
        return null;
    }
  }

  if (portal === "customer") {
    switch (base) {
      case "settings":
      case "preferences":
        return ["notice.view", "notice.update"];
      default:
        return null;
    }
  }

  return null;
}
