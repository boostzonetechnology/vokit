import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type { PayoutRecord, WalletBuckets } from "@/features/payouts/types";

export type LedgerEntry = {
  id: string;
  kind?: string;
  amount_minor?: number;
  currency?: string;
  invoice_id?: string | null;
  payment_id?: string | null;
  reason?: string;
  earned_at?: string | null;
  available_at?: string | null;
  state?: string;
  eligible_base_minor?: number;
  rate_bps_snapshot?: number;
};

export type PayoutReceipt = {
  receipt_number?: string;
  payout_id?: string;
  agency_id?: string;
  amount_minor?: number;
  currency?: string;
  method_label?: string;
  transaction_ref?: string;
  status?: string;
  requested_at?: string | null;
  paid_at?: string | null;
};

function idempotencyKey(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function useAgencyWalletPayouts() {
  const [buckets, setBuckets] = useState<WalletBuckets | null>(null);
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [payouts, setPayouts] = useState<PayoutRecord[]>([]);
  const [receipt, setReceipt] = useState<PayoutReceipt | null>(null);
  const [selectedPayoutId, setSelectedPayoutId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [wallet, payoutRows] = await Promise.all([
        apiGet<{ buckets?: WalletBuckets; entries?: LedgerEntry[] }>("/api/v1/agency/wallet"),
        asList<PayoutRecord>(await apiGet<unknown>("/api/v1/agency/payouts")),
      ]);
      setBuckets(wallet.buckets ?? null);
      setEntries(Array.isArray(wallet.entries) ? wallet.entries : []);
      setPayouts(payoutRows);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load wallet.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filteredPayouts = useMemo(() => {
    const q = query.trim().toLowerCase();
    return payouts.filter((row) => {
      if (statusFilter && (row.status ?? "") !== statusFilter) return false;
      if (!q) return true;
      return [row.id, row.status, row.method_label, row.receipt_number, row.transaction_ref]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [payouts, query, statusFilter]);

  const selectedPayout =
    filteredPayouts.find((row) => row.id === selectedPayoutId) ??
    payouts.find((row) => row.id === selectedPayoutId) ??
    null;

  async function requestWithdrawal(amountMinor: number, methodLabel: string) {
    setBusy(true);
    setMessage("");
    try {
      const created = await apiSend<PayoutRecord>(
        "/api/v1/agency/payouts",
        "POST",
        { amount_minor: amountMinor, method_label: methodLabel },
        { "Idempotency-Key": idempotencyKey("payout") },
      );
      setMessage("Withdrawal requested from available balance.");
      await reload();
      if (created.id) setSelectedPayoutId(created.id);
      return created;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Withdrawal failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function loadReceipt(payoutId: string) {
    setBusy(true);
    setMessage("");
    try {
      const data = await apiGet<PayoutReceipt>(`/api/v1/agency/payouts/${payoutId}/receipt`);
      setReceipt(data);
      setMessage("Receipt loaded.");
      return data;
    } catch (cause) {
      setReceipt(null);
      setMessage(isApiError(cause) ? cause.message : "Receipt unavailable.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    buckets,
    entries,
    payouts: filteredPayouts,
    selectedPayout,
    selectedPayoutId,
    setSelectedPayoutId,
    receipt,
    setReceipt,
    error,
    message,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    reload,
    requestWithdrawal,
    loadReceipt,
  };
}
