import { lazy, Suspense, type ReactNode } from "react";

import { isCustomersRoute } from "@/features/customers/lib/routes";
import { renderAgencyCustomerRoutes } from "@/features/customers/renderAgencyCustomerRoutes";
import { ModuleFallback } from "@/routes/ModuleFallback";

const AgencyAgentsScreen = lazy(() =>
  import("@/features/agents/AgencyAgentsScreen").then((m) => ({
    default: m.AgencyAgentsScreen,
  })),
);

const AgencyNumbersScreen = lazy(() =>
  import("@/features/numbers/AgencyNumbersScreen").then((m) => ({
    default: m.AgencyNumbersScreen,
  })),
);

const AgencyCallsScreen = lazy(() =>
  import("@/features/calls/AgencyCallsScreen").then((m) => ({
    default: m.AgencyCallsScreen,
  })),
);

const AgencyTransfersScreen = lazy(() =>
  import("@/features/transfers/AgencyTransfersScreen").then((m) => ({
    default: m.AgencyTransfersScreen,
  })),
);

const AgencyKnowledgeScreen = lazy(() =>
  import("@/features/knowledge/AgencyKnowledgeScreen").then((m) => ({
    default: m.AgencyKnowledgeScreen,
  })),
);

const AgencyIntegrationsScreen = lazy(() =>
  import("@/features/integrations/AgencyIntegrationsScreen").then((m) => ({
    default: m.AgencyIntegrationsScreen,
  })),
);

const AgencyWebhooksScreen = lazy(() =>
  import("@/features/integrations/AgencyWebhooksScreen").then((m) => ({
    default: m.AgencyWebhooksScreen,
  })),
);

const AgencyBillingScreen = lazy(() =>
  import("@/features/billing/AgencyBillingScreen").then((m) => ({
    default: m.AgencyBillingScreen,
  })),
);

const AgencyWalletScreen = lazy(() =>
  import("@/features/payouts/AgencyWalletScreen").then((m) => ({
    default: m.AgencyWalletScreen,
  })),
);

const AgencyPayoutsScreen = lazy(() =>
  import("@/features/payouts/AgencyPayoutsScreen").then((m) => ({
    default: m.AgencyPayoutsScreen,
  })),
);

const AgencyKycScreen = lazy(() =>
  import("@/features/kyc/AgencyKycScreen").then((m) => ({
    default: m.AgencyKycScreen,
  })),
);

const AgencyTeamScreen = lazy(() =>
  import("@/features/users/AgencyTeamScreen").then((m) => ({
    default: m.AgencyTeamScreen,
  })),
);

const AgencySettingsScreen = lazy(() =>
  import("@/features/notifications/AgencySettingsScreen").then((m) => ({
    default: m.AgencySettingsScreen,
  })),
);

const AgencyNotificationsScreen = lazy(() =>
  import("@/features/notifications/AgencySettingsScreen").then((m) => ({
    default: m.AgencyNotificationsScreen,
  })),
);

function renderLazy(screen: ReactNode) {
  return <Suspense fallback={<ModuleFallback />}>{screen}</Suspense>;
}

/** Agency portal dedicated screens. Returns null when route should use legacy fallback. */
export function renderAgencyProductScreen(route: string): ReactNode | null {
  if (isCustomersRoute(route)) {
    return renderAgencyCustomerRoutes(route);
  }

  const agencyScreens: Record<string, ReactNode> = {
    agents: <AgencyAgentsScreen />,
    numbers: <AgencyNumbersScreen />,
    calls: <AgencyCallsScreen />,
    transfers: <AgencyTransfersScreen />,
    knowledge: <AgencyKnowledgeScreen />,
    integrations: <AgencyIntegrationsScreen />,
    webhooks: <AgencyWebhooksScreen />,
    plans: <AgencyBillingScreen initialTab="plans" />,
    invoices: <AgencyBillingScreen initialTab="invoices" />,
    wallet: <AgencyWalletScreen />,
    payouts: <AgencyPayoutsScreen />,
    kyc: <AgencyKycScreen />,
    team: <AgencyTeamScreen />,
    notifications: <AgencyNotificationsScreen />,
    preferences: <AgencySettingsScreen initialTab="preferences" />,
    settings: <AgencySettingsScreen initialTab="preferences" />,
  };

  if (route in agencyScreens) {
    return renderLazy(agencyScreens[route]);
  }

  return null;
}
