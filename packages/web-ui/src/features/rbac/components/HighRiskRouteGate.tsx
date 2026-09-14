import { usePermissions } from "@/features/auth/hooks/usePermissions";
import { highRiskPermissionsForRoute } from "@/features/rbac/lib/highRiskNav";
import type { Portal } from "@/api";
import type { ReactNode } from "react";

/** Blocks deep-links to high-risk routes without UX permission (server still authoritative). */
export function HighRiskRouteGate({
  portal,
  route,
  children,
}: {
  portal: Portal;
  route: string;
  children: ReactNode;
}) {
  const { canAny } = usePermissions();
  const required = highRiskPermissionsForRoute(portal, route);
  if (required && !canAny(required)) {
    return (
      <article className="mx-auto max-w-lg rounded-xl border border-border-default bg-surface p-6">
        <h1 className="m-0 text-[1.35rem] font-bold text-text-primary">Access restricted</h1>
        <p className="mt-2 mb-0 text-body text-text-muted">
          Your role does not include the permissions required for this module. If you believe this
          is an error, contact a Super Admin.
        </p>
        <p className="mt-3 mb-0 font-mono text-body-sm text-text-muted">
          Required (any): {required.join(", ")}
        </p>
      </article>
    );
  }
  return children;
}
