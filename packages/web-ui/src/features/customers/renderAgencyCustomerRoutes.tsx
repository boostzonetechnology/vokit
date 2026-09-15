import { lazy, Suspense } from "react";

import { PageContentSkeleton } from "@/components/ui/PageContentSkeleton";
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
  return <PageContentSkeleton />;
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
