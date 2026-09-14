import { useCallback, useMemo } from "react";

import { useSessionOptional } from "@/features/auth/context/SessionContext";

/**
 * UX-only permission helpers. Server authorization remains authoritative.
 * Super Admin: is_super_admin + empty permissions[] still grants can() = true.
 */
export function usePermissions() {
  const session = useSessionOptional();

  const isSuperAdmin = Boolean(session?.is_super_admin);
  const permissions = session?.permissions ?? [];
  const permissionSet = useMemo(() => new Set(permissions), [permissions]);

  const can = useCallback(
    (code: string) => {
      if (!session) return false;
      if (isSuperAdmin) return true;
      return permissionSet.has(code);
    },
    [session, isSuperAdmin, permissionSet],
  );

  const canAny = useCallback(
    (codes: string[]) => {
      if (!session) return false;
      if (isSuperAdmin) return true;
      return codes.some((code) => permissionSet.has(code));
    },
    [session, isSuperAdmin, permissionSet],
  );

  const canAll = useCallback(
    (codes: string[]) => {
      if (!session) return false;
      if (isSuperAdmin) return true;
      return codes.every((code) => permissionSet.has(code));
    },
    [session, isSuperAdmin, permissionSet],
  );

  return {
    session,
    isSuperAdmin,
    permissions,
    can,
    canAny,
    canAll,
  };
}
