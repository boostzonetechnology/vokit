import { lazy, Suspense } from "react";

import { isCustomersRoute, parseCustomerRoute } from "@/features/customers/lib/routes";

const AgencyCustomersScreen = lazy(() =>
  import("@/features/customers/AgencyCustomersScreen").then((m) => ({
    default: m.AgencyCustomersScreen,
  })),
);
const AgencyCustomerCreateScreen = lazy(() =>
  import("@/features/customers/AgencyCustomerCreateScreen").then((m) => ({
    default: m.AgencyCustomerCreateScreen,
  })),
);
const AgencyCustomerDetailScreen = lazy(() =>
  import("@/features/customers/AgencyCustomerDetailScreen").then((m) => ({
    default: m.AgencyCustomerDetailScreen,
  })),
);

function ScreenFallback() {
  return (
    <p className="m-0 p-2 text-body text-text-muted" role="status">
      Loading module…
    </p>
  );
}

export function renderAgencyCustomerRoutes(route: string) {
  if (!isCustomersRoute(route)) return null;
  const parsed = parseCustomerRoute(route);
  if (!parsed) return null;

  if (parsed.kind === "create") {
    return (
      <Suspense fallback={<ScreenFallback />}>
        <AgencyCustomerCreateScreen />
      </Suspense>
    );
  }
  if (parsed.kind === "detail") {
    return (
      <Suspense fallback={<ScreenFallback />}>
        <AgencyCustomerDetailScreen customerId={parsed.customerId} />
      </Suspense>
    );
  }
  return (
    <Suspense fallback={<ScreenFallback />}>
      <AgencyCustomersScreen />
    </Suspense>
  );
}
