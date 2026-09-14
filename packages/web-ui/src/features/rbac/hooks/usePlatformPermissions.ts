import { useCallback, useEffect, useMemo, useState } from "react";

import { isApiError } from "@/api";
import {
  createPlatformPermission,
  listPlatformPermissions,
  syncPlatformPermissions,
} from "@/features/rbac/services/rbac.service";
import type { PermissionRecord } from "@/features/rbac/types/rbac.types";

export function usePlatformPermissions() {
  const [permissions, setPermissions] = useState<PermissionRecord[]>([]);
  const [namespace, setNamespace] = useState("");
  const [module, setModule] = useState("");
  const [sensitiveOnly, setSensitiveOnly] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await listPlatformPermissions({
        namespace: namespace || undefined,
        module: module || undefined,
      });
      setPermissions(rows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load permissions.");
      setPermissions([]);
    } finally {
      setLoading(false);
    }
  }, [namespace, module]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    if (!sensitiveOnly) return permissions;
    return permissions.filter((row) => row.is_sensitive);
  }, [permissions, sensitiveOnly]);

  async function createPermission(input: {
    namespace: string;
    code: string;
    description: string;
    is_sensitive: boolean;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const created = await createPlatformPermission(input);
      setMessage(`Permission “${created.code}” created.`);
      await reload();
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create permission failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function syncCatalog() {
    setBusy(true);
    setMessage("");
    try {
      const result = await syncPlatformPermissions();
      setMessage(
        `Catalog synced. Permissions: ${result.permission_count}. Roles: ${result.role_count}.`,
      );
      await reload();
      return result;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Sync failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    permissions: filtered,
    allPermissions: permissions,
    namespace,
    setNamespace,
    module,
    setModule,
    sensitiveOnly,
    setSensitiveOnly,
    error,
    message,
    loading,
    busy,
    reload,
    createPermission,
    syncCatalog,
  };
}
