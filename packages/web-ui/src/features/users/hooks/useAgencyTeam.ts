import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";

export type TeamMember = {
  id: string;
  membership_id?: string;
  email?: string;
  principal_type?: string;
  role?: string;
  tenant_id?: string | null;
  customer_id?: string | null;
  status?: string;
};

export const AGENCY_ROLES = [
  { value: "agency_owner", label: "Owner" },
  { value: "agency_admin", label: "Admin" },
  { value: "agency_agent_builder", label: "Agent builder" },
  { value: "agency_finance", label: "Finance" },
] as const;

export function useAgencyTeam() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = asList<TeamMember>(await apiGet<unknown>("/api/v1/agency/team"));
      setMembers(rows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load team.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return members.filter((row) => {
      if (roleFilter && (row.role ?? "") !== roleFilter) return false;
      if (!q) return true;
      return [row.email, row.role, row.status, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [members, query, roleFilter]);

  const selected = members.find((row) => row.id === selectedId) ?? null;

  async function invite(input: { email: string; role: string }) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend("/api/v1/agency/team", "POST", {
        email: input.email,
        role: input.role,
      });
      setMessage("Invitation sent.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Invite failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function revoke(userId: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/agency/team/${userId}/disable`, "POST", {});
      setMessage("User access disabled and sessions revoked.");
      if (selectedId === userId) setSelectedId("");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Revoke failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    members: filtered,
    selected,
    selectedId,
    setSelectedId,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    roleFilter,
    setRoleFilter,
    reload,
    invite,
    revoke,
  };
}
