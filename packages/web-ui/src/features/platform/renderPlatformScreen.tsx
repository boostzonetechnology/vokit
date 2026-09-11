import { lazy, Suspense, type ComponentType, type ReactNode } from "react";

import { isAgenciesRoute } from "@/features/agencies/lib/routes";
import { renderAgencyRoutes } from "@/features/agencies/renderAgencyRoutes";

const PlatformAgentsScreen = lazy(() =>
  import("@/features/agents/PlatformAgentsScreen").then((m) => ({ default: m.PlatformAgentsScreen })),
);
const PlatformCustomersScreen = lazy(() =>
  import("@/features/customers/PlatformCustomersScreen").then((m) => ({
    default: m.PlatformCustomersScreen,
  })),
);
const PlatformTemplatesScreen = lazy(() =>
  import("@/features/templates/PlatformTemplatesScreen").then((m) => ({
    default: m.PlatformTemplatesScreen,
  })),
);
const PlatformInstructionsScreen = lazy(() =>
  import("@/features/instructions/PlatformInstructionsScreen").then((m) => ({
    default: m.PlatformInstructionsScreen,
  })),
);
const PlatformKnowledgeScreen = lazy(() =>
  import("@/features/knowledge/PlatformKnowledgeScreen").then((m) => ({
    default: m.PlatformKnowledgeScreen,
  })),
);
const PlatformNumbersScreen = lazy(() =>
  import("@/features/numbers/PlatformNumbersScreen").then((m) => ({ default: m.PlatformNumbersScreen })),
);
const PlatformTransfersScreen = lazy(() =>
  import("@/features/transfers/PlatformTransfersScreen").then((m) => ({
    default: m.PlatformTransfersScreen,
  })),
);
const PlatformPlansScreen = lazy(() =>
  import("@/features/plans/PlatformPlansScreen").then((m) => ({ default: m.PlatformPlansScreen })),
);
const PlatformBillingScreen = lazy(() =>
  import("@/features/billing/PlatformBillingScreen").then((m) => ({ default: m.PlatformBillingScreen })),
) as unknown as ComponentType<{ route?: string }>;
const PlatformPayoutsScreen = lazy(() =>
  import("@/features/payouts/PlatformPayoutsScreen").then((m) => ({ default: m.PlatformPayoutsScreen })),
);
const PlatformCallsScreen = lazy(() =>
  import("@/features/calls/PlatformCallsScreen").then((m) => ({ default: m.PlatformCallsScreen })),
);
const PlatformIntegrationsScreen = lazy(() =>
  import("@/features/integrations/PlatformIntegrationsScreen").then((m) => ({
    default: m.PlatformIntegrationsScreen,
  })),
);
const PlatformNotificationsScreen = lazy(() =>
  import("@/features/notifications/PlatformNotificationsScreen").then((m) => ({
    default: m.PlatformNotificationsScreen,
  })),
) as unknown as ComponentType<{ route?: string }>;
const PlatformAuditScreen = lazy(() =>
  import("@/features/audit/PlatformAuditScreen").then((m) => ({ default: m.PlatformAuditScreen })),
);
const PlatformUsersScreen = lazy(() =>
  import("@/features/users/PlatformUsersScreen").then((m) => ({ default: m.PlatformUsersScreen })),
);
const PlatformSettingsScreen = lazy(() =>
  import("@/features/settings/PlatformSettingsScreen").then((m) => ({
    default: m.PlatformSettingsScreen,
  })),
);
const PlatformKycScreen = lazy(() =>
  import("@/features/kyc/PlatformKycScreen").then((m) => ({ default: m.PlatformKycScreen })),
);
const PlatformResourceScreen = lazy(() =>
  import("./PlatformResourceScreen").then((m) => ({
    default: m.PlatformResourceScreen,
  })),
) as unknown as ComponentType<{ route: string }>;

function ScreenFallback() {
  return (
    <p className="m-0 p-2 text-body text-text-muted" role="status">
      Loading module…
    </p>
  );
}

function Lazy({ children }: { children: ReactNode }) {
  return <Suspense fallback={<ScreenFallback />}>{children}</Suspense>;
}

/** Platform-only product routes — code-split per module. */
export function renderPlatformProductScreen(route: string): ReactNode | null {
  if (isAgenciesRoute(route)) {
    return renderAgencyRoutes(route);
  }

  switch (route) {
    case "agents":
      return (
        <Lazy>
          <PlatformAgentsScreen />
        </Lazy>
      );
    case "customers":
      return (
        <Lazy>
          <PlatformCustomersScreen />
        </Lazy>
      );
    case "templates":
      return (
        <Lazy>
          <PlatformTemplatesScreen />
        </Lazy>
      );
    case "instructions":
      return (
        <Lazy>
          <PlatformInstructionsScreen />
        </Lazy>
      );
    case "knowledge":
      return (
        <Lazy>
          <PlatformKnowledgeScreen />
        </Lazy>
      );
    case "numbers":
      return (
        <Lazy>
          <PlatformNumbersScreen />
        </Lazy>
      );
    case "transfers":
      return (
        <Lazy>
          <PlatformTransfersScreen />
        </Lazy>
      );
    case "plans":
      return (
        <Lazy>
          <PlatformPlansScreen />
        </Lazy>
      );
    case "payments":
    case "invoices":
    case "disputes":
      return (
        <Lazy>
          <PlatformBillingScreen route={route} />
        </Lazy>
      );
    case "payouts":
      return (
        <Lazy>
          <PlatformPayoutsScreen />
        </Lazy>
      );
    case "calls":
      return (
        <Lazy>
          <PlatformCallsScreen />
        </Lazy>
      );
    case "integrations":
      return (
        <Lazy>
          <PlatformIntegrationsScreen />
        </Lazy>
      );
    case "notifications":
    case "notice-templates":
      return (
        <Lazy>
          <PlatformNotificationsScreen route={route} />
        </Lazy>
      );
    case "audit":
      return (
        <Lazy>
          <PlatformAuditScreen />
        </Lazy>
      );
    case "users":
      return (
        <Lazy>
          <PlatformUsersScreen />
        </Lazy>
      );
    case "settings":
      return (
        <Lazy>
          <PlatformSettingsScreen />
        </Lazy>
      );
    case "kyc":
      return (
        <Lazy>
          <PlatformKycScreen />
        </Lazy>
      );
    default:
      return null;
  }
}

export function renderPlatformResourceScreen(route: string): ReactNode {
  return (
    <Lazy>
      <PlatformResourceScreen route={route} />
    </Lazy>
  );
}
