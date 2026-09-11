import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { PlatformInvitation, PlatformUser } from "@/features/users/types";

export function usePlatformUsers() {
  const [users, setUsers] = useState<PlatformUser[]>([]);
  const [invitations, setInvitations] = useState<PlatformInvitation[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [userRows, inviteRows] = await Promise.all([
        asList<PlatformUser>(await apiGet<unknown>("/api/v1/platform/users")),
        asList<PlatformInvitation>(await apiGet<unknown>("/api/v1/platform/invitations")),
      ]);
      setUsers(userRows);
      setInvitations(inviteRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load users.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return users.filter((row) => {
      if (statusFilter && (row.status ?? "") !== statusFilter) return false;
      if (!q) return true;
      return [row.email, row.role, row.status, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [users, query, statusFilter]);

  const selected = users.find((row) => row.id === selectedId) ?? null;

  async function inviteUser(input: {
    email: string;
    role: string;
    principal_type: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<PlatformInvitation>("/api/v1/platform/users", "POST", {
        email: input.email,
        role: input.role,
        principal_type: input.principal_type,
      });
      setMessage(
        created.token
          ? `Invitation created. One-time token returned once: ${created.token}`
          : "Invitation created.",
      );
      await reload();
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Invite failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function disableUser(userId: string) {
    setBusy(true);
    setMessage("");
    try {
      const result = await apiSend<{ sessions_revoked?: number }>(
        `/api/v1/platform/users/${userId}/disable`,
        "POST",
        {},
      );
      setMessage(
        `User disabled. Sessions revoked: ${result.sessions_revoked ?? 0}.`,
      );
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Disable failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    users: filtered,
    invitations,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    reload,
    inviteUser,
    disableUser,
  };
}
