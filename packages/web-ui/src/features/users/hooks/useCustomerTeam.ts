import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";

export type CustomerTeamMember = {
  id: string;
  membership_id?: string;
  email?: string;
  role?: string;
  status?: string;
};

export const CUSTOMER_ROLES = [
  { value: "customer_owner", label: "Owner" },
  { value: "customer_admin", label: "Admin" },
  { value: "customer_analyst", label: "Analyst" },
] as const;

export type CustomerAccount = {
  display_name?: string;
  legal_name?: string;
  owner_email?: string;
  phone?: string;
  country?: string;
  timezone?: string;
  status?: string;
};

export function useCustomerTeam() {
  const [members, setMembers] = useState<CustomerTeamMember[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = asList<CustomerTeamMember>(await apiGet<unknown>("/api/v1/customer/team"));
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
    if (!q) return members;
    return members.filter((row) =>
      [row.email, row.role, row.status, row.id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [members, query]);

  const selected = members.find((row) => row.id === selectedId) ?? null;

  async function invite(input: { email: string; role: string }) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend("/api/v1/customer/team", "POST", input);
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
      await apiSend(`/api/v1/customer/team/${userId}/disable`, "POST", {});
      setMessage("User access disabled.");
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
    reload,
    invite,
    revoke,
  };
}

export function useCustomerAccount() {
  const [account, setAccount] = useState<CustomerAccount | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiGet<CustomerAccount>("/api/v1/customer/account");
      setAccount(data);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load account.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { account, error, loading, reload };
}
