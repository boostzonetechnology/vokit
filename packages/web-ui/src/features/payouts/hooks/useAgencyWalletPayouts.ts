import { useCallback, useEffect, useMemo, useState } from "react";

import { mapPayoutError } from "@/features/payouts/lib/mapPayoutError";
import {
  getAgencyPayoutProof,
  getAgencyPayoutReceipt,
  getAgencyWallet,
  listAgencyPayouts,
  requestAgencyPayout,
} from "@/features/payouts/services/wallet.service";
import type {
  LedgerEntry,
  PayoutProof,
  PayoutReceipt,
  PayoutRecord,
  WalletBuckets,
} from "@/features/payouts/types";

export function useAgencyWalletPayouts() {
  const [buckets, setBuckets] = useState<WalletBuckets | null>(null);
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [payouts, setPayouts] = useState<PayoutRecord[]>([]);
  const [receipt, setReceipt] = useState<PayoutReceipt | null>(null);
  const [proof, setProof] = useState<PayoutProof | null>(null);
  const [proofUnavailable, setProofUnavailable] = useState(false);
  const [selectedPayoutId, setSelectedPayoutId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [ledgerKind, setLedgerKind] = useState("");
  const [ledgerState, setLedgerState] = useState("");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [wallet, payoutRows] = await Promise.all([getAgencyWallet(), listAgencyPayouts()]);
      setBuckets(wallet.buckets);
      setEntries(wallet.entries);
      setPayouts(payoutRows);
      setError("");
    } catch (cause) {
      setError(mapPayoutError(cause, "Failed to load wallet."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const filteredEntries = useMemo(() => {
    return entries.filter((row) => {
      if (ledgerKind && (row.kind ?? "") !== ledgerKind) return false;
      if (ledgerState) {
        const state = (row.state ?? "").toLowerCase();
        if (ledgerState === "on_hold") {
          if (state !== "on_hold" && state !== "held") return false;
        } else if (state !== ledgerState) {
          return false;
        }
      }
      return true;
    });
  }, [entries, ledgerKind, ledgerState]);

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

  async function requestWithdrawal(amountMinor: number, payoutMethodId: string) {
    setBusy(true);
    setMessage("");
    try {
      const created = await requestAgencyPayout({
        amount_minor: amountMinor,
        payout_method_id: payoutMethodId,
      });
      setMessage("Withdrawal requested from available balance.");
      await reload();
      if (created.id) setSelectedPayoutId(created.id);
      return created;
    } catch (cause) {
      setMessage(mapPayoutError(cause, "Withdrawal failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function loadReceipt(payoutId: string) {
    setBusy(true);
    setMessage("");
    try {
      const data = await getAgencyPayoutReceipt(payoutId);
      setReceipt(data);
      setMessage("Receipt loaded.");
      return data;
    } catch (cause) {
      setReceipt(null);
      setMessage(mapPayoutError(cause, "Receipt unavailable."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function ensureReceipt(payoutId: string): Promise<PayoutReceipt> {
    if (receipt?.payout_id === payoutId) return receipt;
    return loadReceipt(payoutId);
  }

  async function loadProof(payoutId: string) {
    setBusy(true);
    setMessage("");
    setProofUnavailable(false);
    try {
      const data = await getAgencyPayoutProof(payoutId);
      if (data == null) {
        setProof(null);
        setProofUnavailable(true);
        setMessage("Platform has not shared proof for this payout.");
        return null;
      }
      setProof(data);
      setProofUnavailable(false);
      setMessage("Shared admin proof loaded.");
      return data;
    } catch (cause) {
      setProof(null);
      setProofUnavailable(true);
      setMessage(mapPayoutError(cause, "Proof unavailable."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    buckets,
    entries: filteredEntries,
    payouts: filteredPayouts,
    allPayouts: payouts,
    selectedPayout,
    selectedPayoutId,
    setSelectedPayoutId,
    receipt,
    setReceipt,
    proof,
    setProof,
    proofUnavailable,
    error,
    message,
    setMessage,
    loading,
    busy,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    ledgerKind,
    setLedgerKind,
    ledgerState,
    setLedgerState,
    reload,
    requestWithdrawal,
    loadReceipt,
    ensureReceipt,
    loadProof,
  };
}
