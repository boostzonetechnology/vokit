import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList, safeGetList } from "@/features/platform/lib/list";
import type { AgencyOption, PayoutProof, PayoutRecord, WalletBuckets } from "@/features/payouts/types";

export function usePlatformPayouts() {
  const [payouts, setPayouts] = useState<PayoutRecord[]>([]);
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [agencyId, setAgencyId] = useState("");
  const [wallet, setWallet] = useState<WalletBuckets | null>(null);
  const [proof, setProof] = useState<PayoutProof | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("requested");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      const qs = params.toString();
      const [rows, agencyRows] = await Promise.all([
        asList<PayoutRecord>(
          await apiGet<unknown>(`/api/v1/platform/payouts${qs ? `?${qs}` : ""}`),
        ),
        safeGetList<AgencyOption>("/api/v1/platform/agencies", (path) => apiGet(path)),
      ]);
      setPayouts(rows);
      setAgencies(agencyRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load payouts.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const loadWallet = useCallback(async (id: string) => {
    if (!id) {
      setWallet(null);
      return;
    }
    try {
      const data = await apiGet<{ buckets?: WalletBuckets }>(
        `/api/v1/platform/agencies/${id}/wallet`,
      );
      setWallet(data.buckets ?? null);
    } catch (cause) {
      setWallet(null);
      setMessage(isApiError(cause) ? cause.message : "Failed to load wallet.");
    }
  }, []);

  useEffect(() => {
    void loadWallet(agencyId);
  }, [agencyId, loadWallet]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return payouts;
    return payouts.filter((row) =>
      [row.id, row.agency_id, row.status, row.method_label, row.receipt_number]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [payouts, query]);

  const selected = payouts.find((row) => row.id === selectedId) ?? null;

  async function runAction(payoutId: string, action: string, transactionRef = "") {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/payouts/${payoutId}/action`, "POST", {
        action,
        transaction_ref: transactionRef,
      });
      setMessage(`Payout ${action} completed.`);
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Action failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function markPaid(payoutId: string, transactionRef: string) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/payouts/${payoutId}/mark-paid`, "POST", {
        transaction_ref: transactionRef,
      });
      setMessage("Payout marked paid. Agency receipt is generated server-side.");
      await reload();
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Mark paid failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function uploadProof(
    payoutId: string,
    input: { object_ref: string; content_type: string; checksum: string },
  ) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<PayoutProof>(
        `/api/v1/platform/payouts/${payoutId}/proof`,
        "POST",
        input,
      );
      setProof(created);
      setMessage("Private payout proof uploaded.");
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Proof upload failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function loadProof(payoutId: string) {
    try {
      const data = await apiGet<PayoutProof>(`/api/v1/platform/payouts/${payoutId}/proof`);
      setProof(data);
    } catch {
      setProof(null);
    }
  }

  async function adjustWallet(input: {
    agencyId: string;
    amount_minor: number;
    direction: string;
    reason: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/agencies/${input.agencyId}/wallet/adjust`, "POST", {
        amount_minor: input.amount_minor,
        direction: input.direction,
        reason: input.reason,
      });
      setMessage("Audited wallet adjustment recorded.");
      await loadWallet(input.agencyId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Adjustment failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function freezeWallet(input: { agencyId: string; frozen: boolean; reason: string }) {
    setBusy(true);
    setMessage("");
    try {
      await apiSend(`/api/v1/platform/agencies/${input.agencyId}/wallet/freeze`, "POST", {
        frozen: input.frozen,
        reason: input.reason,
      });
      setMessage(input.frozen ? "Wallet frozen." : "Wallet unfrozen.");
      await loadWallet(input.agencyId);
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Freeze failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    payouts: filtered,
    agencies,
    selected,
    selectedId,
    setSelectedId,
    agencyId,
    setAgencyId,
    wallet,
    proof,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    reload,
    runAction,
    markPaid,
    uploadProof,
    loadProof,
    adjustWallet,
    freezeWallet,
  };
}
