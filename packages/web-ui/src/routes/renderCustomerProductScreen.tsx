import { lazy, Suspense, type ReactNode } from "react";

import { ModuleFallback } from "@/routes/ModuleFallback";

const CustomerAgentsScreen = lazy(() =>
  import("@/features/agents/CustomerAgentsScreen").then((m) => ({
    default: m.CustomerAgentsScreen,
  })),
);

const CustomerCallsScreen = lazy(() =>
  import("@/features/calls/CustomerCallsScreen").then((m) => ({
    default: m.CustomerCallsScreen,
  })),
);

const CustomerUsageScreen = lazy(() =>
  import("@/features/billing/CustomerBillingScreens").then((m) => ({
    default: m.CustomerUsageScreen,
  })),
);

const CustomerInvoicesScreen = lazy(() =>
  import("@/features/billing/CustomerBillingScreens").then((m) => ({
    default: m.CustomerInvoicesScreen,
  })),
);

const CustomerPaymentMethodsScreen = lazy(() =>
  import("@/features/billing/CustomerBillingScreens").then((m) => ({
    default: m.CustomerPaymentMethodsScreen,
  })),
);

const CustomerKnowledgeScreen = lazy(() =>
  import("@/features/knowledge/CustomerKnowledgeScreen").then((m) => ({
    default: m.CustomerKnowledgeScreen,
  })),
);

const CustomerIntegrationsScreen = lazy(() =>
  import("@/features/integrations/CustomerIntegrationsScreen").then((m) => ({
    default: m.CustomerIntegrationsScreen,
  })),
);

const CustomerTeamScreen = lazy(() =>
  import("@/features/users/CustomerTeamScreen").then((m) => ({
    default: m.CustomerTeamScreen,
  })),
);

const CustomerProfileScreen = lazy(() =>
  import("@/features/users/CustomerTeamScreen").then((m) => ({
    default: m.CustomerProfileScreen,
  })),
);

const CustomerSettingsScreen = lazy(() =>
  import("@/features/notifications/CustomerSettingsScreen").then((m) => ({
    default: m.CustomerSettingsScreen,
  })),
);

const CustomerNotificationsScreen = lazy(() =>
  import("@/features/notifications/CustomerSettingsScreen").then((m) => ({
    default: m.CustomerNotificationsScreen,
  })),
);

function renderLazy(screen: ReactNode) {
  return <Suspense fallback={<ModuleFallback />}>{screen}</Suspense>;
}

/** Customer portal dedicated screens. Returns null when route should use legacy fallback. */
export function renderCustomerProductScreen(route: string): ReactNode | null {
  const customerScreens: Record<string, ReactNode> = {
    agents: <CustomerAgentsScreen />,
    calls: <CustomerCallsScreen />,
    usage: <CustomerUsageScreen />,
    invoices: <CustomerInvoicesScreen />,
    "payment-methods": <CustomerPaymentMethodsScreen />,
    knowledge: <CustomerKnowledgeScreen />,
    integrations: <CustomerIntegrationsScreen />,
    team: <CustomerTeamScreen />,
    account: <CustomerProfileScreen />,
    notifications: <CustomerNotificationsScreen />,
    preferences: <CustomerSettingsScreen initialTab="preferences" />,
    settings: <CustomerSettingsScreen initialTab="preferences" />,
  };

  if (route in customerScreens) {
    return renderLazy(customerScreens[route]);
  }

  return null;
}
