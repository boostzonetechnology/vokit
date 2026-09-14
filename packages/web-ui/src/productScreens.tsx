import type { ReactNode } from "react";

import { Portal } from "@/api";
import {
  renderPlatformProductScreen,
  renderPlatformResourceScreen,
} from "@/features/platform/renderPlatformScreen";
import { PLATFORM_MODULES } from "@/features/platform/platformModules";
import { renderAgencyProductScreen } from "@/routes/renderAgencyProductScreen";
import { renderCustomerProductScreen } from "@/routes/renderCustomerProductScreen";
import { renderLegacyProductScreen } from "@/routes/legacy/legacyProductScreens";

export function renderProductScreen(
  portal: Portal,
  route: string,
  fallbackPath: string,
  fallbackTitle: string,
): ReactNode {
  if (portal === "platform") {
    const custom = renderPlatformProductScreen(route);
    if (custom) return custom;
    if (route in PLATFORM_MODULES) {
      return renderPlatformResourceScreen(route);
    }
  }

  if (portal === "agency") {
    const agency = renderAgencyProductScreen(route);
    if (agency) return agency;
  }

  if (portal === "customer") {
    const customer = renderCustomerProductScreen(route);
    if (customer) return customer;
  }

  return renderLegacyProductScreen(portal, route, fallbackPath, fallbackTitle);
}
