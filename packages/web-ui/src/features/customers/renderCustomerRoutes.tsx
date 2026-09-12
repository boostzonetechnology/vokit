import { lazy, Suspense } from "react";

import { isCustomersRoute, parseCustomerRoute } from "@/features/customers/lib/routes";

const PlatformCustomersScreen = lazy(() =>
  import("@/features/customers/PlatformCustomersScreen").then((m) => ({
    default: m.PlatformCustomersScreen,
  })),
);
const PlatformCustomerCreateScreen = lazy(() =>
  import("@/features/customers/PlatformCustomerCreateScreen").then((m) => ({
    default: m.PlatformCustomerCreateScreen,
  })),
);
const PlatformCustomerDetailScreen = lazy(() =>
  import("@/features/customers/PlatformCustomerDetailScreen").then((m) => ({
    default: m.PlatformCustomerDetailScreen,
  })),
);

function ScreenFallback() {
  return (
    <p className="m-0 p-2 text-body text-text-muted" role="status">
      Loading module…
    </p>
  );
}

export function renderCustomerRoutes(route: string) {
  if (!isCustomersRoute(route)) return null;
  const parsed = parseCustomerRoute(route);
  if (!parsed) return null;

  if (parsed.kind === "create") {
    return (
      <Suspense fallback={<ScreenFallback />}>
        <PlatformCustomerCreateScreen />
      </Suspense>
    );
  }
  if (parsed.kind === "detail") {
    return (
      <Suspense fallback={<ScreenFallback />}>
        <PlatformCustomerDetailScreen customerId={parsed.customerId} />
      </Suspense>
    );
  }
  return (
    <Suspense fallback={<ScreenFallback />}>
      <PlatformCustomersScreen />
    </Suspense>
  );
}
