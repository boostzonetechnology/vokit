import { useCallback, useEffect, useState } from "react";

import { isApiError, type Portal } from "@/api";
import { listPortalRoles } from "@/features/rbac/services/rbac.service";
import type { RoleRecord } from "@/features/rbac/types/rbac.types";

/** Load invite role dropdown options for a portal (or platform namespace filter). */
export function usePortalRoles(portal: Portal, namespace?: string) {
  const [roles, setRoles] = useState<RoleRecord[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const ns =
        portal === "platform" ? (namespace ?? "platform") : undefined;
      const rows = await listPortalRoles(portal, ns);
      setRoles(rows);
      setError("");
    } catch (cause) {
      setRoles([]);
      setError(isApiError(cause) ? cause.message : "Failed to load roles.");
    } finally {
      setLoading(false);
    }
  }, [portal, namespace]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { roles, error, loading, reload };
}
