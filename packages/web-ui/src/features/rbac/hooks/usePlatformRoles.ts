import { useCallback, useEffect, useState } from "react";

import { isApiError } from "@/api";
import {
  createPlatformRole,
  deletePlatformRole,
  getPlatformRole,
  listPlatformRoles,
  updatePlatformRole,
} from "@/features/rbac/services/rbac.service";
import type { RoleRecord } from "@/features/rbac/types/rbac.types";

export function usePlatformRoles(initialNamespace = "") {
  const [roles, setRoles] = useState<RoleRecord[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [selected, setSelected] = useState<RoleRecord | null>(null);
  const [namespace, setNamespace] = useState(initialNamespace);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await listPlatformRoles(namespace || undefined);
      setRoles(rows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load roles.");
      setRoles([]);
    } finally {
      setLoading(false);
    }
  }, [namespace]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (!selectedId) {
      setSelected(null);
      return;
    }
    let active = true;
    void getPlatformRole(selectedId)
      .then((row) => {
        if (active) setSelected(row);
      })
      .catch((cause) => {
        if (active) {
          setSelected(null);
          setError(isApiError(cause) ? cause.message : "Failed to load role.");
        }
      });
    return () => {
      active = false;
    };
  }, [selectedId]);

  async function createRole(input: {
    slug: string;
    display_name: string;
    permissions: string[];
    namespace?: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const created = await createPlatformRole({
        slug: input.slug,
        display_name: input.display_name,
        namespace: input.namespace || "platform",
        permissions: input.permissions,
      });
      setMessage(`Role “${created.slug}” created.`);
      await reload();
      setSelectedId(created.id);
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Create role failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function saveRole(input: { display_name: string; permissions: string[] }) {
    if (!selectedId) return;
    setBusy(true);
    setMessage("");
    try {
      const updated = await updatePlatformRole(selectedId, {
        display_name: input.display_name,
        permissions: input.permissions,
      });
      setMessage(`Role “${updated.slug}” saved.`);
      setSelected(updated);
      await reload();
      return updated;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Update role failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function removeRole(roleId: string) {
    setBusy(true);
    setMessage("");
    try {
      await deletePlatformRole(roleId);
      setMessage("Role deleted.");
      if (selectedId === roleId) setSelectedId("");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Delete role failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    roles,
    selected,
    selectedId,
    setSelectedId,
    namespace,
    setNamespace,
    error,
    message,
    loading,
    busy,
    reload,
    createRole,
    saveRole,
    removeRole,
  };
}
