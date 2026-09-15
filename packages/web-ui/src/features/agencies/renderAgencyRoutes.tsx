import { lazy, Suspense } from "react";

import { PageContentSkeleton } from "@/components/ui/PageContentSkeleton";
import { isAgenciesRoute, parseAgencyRoute } from "@/features/agencies/lib/routes";

const PlatformAgenciesScreen = lazy(() =>
  import("@/features/agencies/PlatformAgenciesScreen").then((m) => ({
    default: m.PlatformAgenciesScreen,
  })),
);
const PlatformAgencyCreateScreen = lazy(() =>
  import("@/features/agencies/PlatformAgencyCreateScreen").then((m) => ({
    default: m.PlatformAgencyCreateScreen,
  })),
);
const PlatformAgencyDetailScreen = lazy(() =>
  import("@/features/agencies/PlatformAgencyDetailScreen").then((m) => ({
    default: m.PlatformAgencyDetailScreen,
  })),
);

function ScreenFallback() {
  return <PageContentSkeleton />;
}

export function renderAgencyRoutes(route: string) {
  if (!isAgenciesRoute(route)) return null;
  const parsed = parseAgencyRoute(route);
  if (!parsed) return null;

  if (parsed.kind === "create") {
    return (
      <Suspense fallback={<ScreenFallback />}>
        <PlatformAgencyCreateScreen />
      </Suspense>
    );
  }
  if (parsed.kind === "detail") {
    return (
      <Suspense fallback={<ScreenFallback />}>
        <PlatformAgencyDetailScreen agencyId={parsed.agencyId} />
      </Suspense>
    );
  }
  return (
    <Suspense fallback={<ScreenFallback />}>
      <PlatformAgenciesScreen />
    </Suspense>
  );
}
