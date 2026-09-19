import { useCallback, useEffect, useMemo, useState } from "react";

import { nameOrId } from "@/features/payouts/lib/display";
import { mapPayoutError } from "@/features/payouts/lib/mapPayoutError";
import {
  adjustAgencyWallet,
  freezeAgencyWallet,
  getPlatformAgencyWallet,
  getPlatformPayoutProof,
  listPlatformPayouts,
  listPayoutAgencies,
  markPlatformPayoutPaid,
  runPlatformPayoutAction,
  setPlatformPayoutProofAgencyVisible,
  uploadPlatformPayoutProof,
} from "@/features/payouts/services/wallet.service";
import type {
  AgencyOption,
  PayoutProof,
  PayoutRecord,
  WalletBuckets,
} from "@/features/payouts/types";

const OPEN_STATUSES = new Set(["requested", "approved", "processing", "frozen"]);

export function usePlatformPayouts() {
  const [payouts, setPayouts] = useState<PayoutRecord[]>([]);
  const [agencies, setAgencies] = useState<AgencyOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [selected, setSelected] = useState<PayoutRecord | null>(null);
  const [agencyId, setAgencyId] = useState("");
  const [wallet, setWallet] = useState<WalletBuckets | null>(null);
  const [proof, setProof] = useState<PayoutProof | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  /** open = queue work; paid/rejected/specific; empty = all */
  const [statusFilter, setStatusFilter] = useState("open");

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const apiStatus =
        statusFilter && statusFilter !== "open" ? statusFilter : undefined;
      const [rows, agencyRows] = await Promise.all([
        listPlatformPayouts({ status: apiStatus }),
        listPayoutAgencies(),
      ]);
      setPayouts(rows);
      setAgencies(agencyRows);
      setError("");
    } catch (cause) {
      setError(mapPayoutError(cause, "Failed to load payouts."));
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (!selectedId) {
      setSelected(null);
      return;
    }
    const match = payouts.find((row) => row.id === selectedId);
    if (match) setSelected(match);
  }, [payouts, selectedId]);

  const agencyLabel = useCallback(
    (id?: string | null) => {
      if (!id) return "—";
      const match = agencies.find((row) => row.id === id);
      return nameOrId(match?.display_name, id);
    },
    [agencies],
  );

  const loadWallet = useCallback(async (id: string) => {
    if (!id) {
      setWallet(null);
      return;
    }
    try {
      setWallet(await getPlatformAgencyWallet(id));
    } catch (cause) {
      setWallet(null);
      setMessage(mapPayoutError(cause, "Failed to load wallet."));
    }
  }, []);

  useEffect(() => {
    void loadWallet(agencyId);
  }, [agencyId, loadWallet]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return payouts.filter((row) => {
      if (statusFilter === "open" && !OPEN_STATUSES.has((row.status ?? "").toLowerCase())) {
        return false;
      }
      if (!q) return true;
      return [
        row.id,
        row.agency_id,
        agencyLabel(row.agency_id),
        row.status,
        row.method_label,
        row.receipt_number,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [payouts, query, agencyLabel, statusFilter]);

  function selectPayout(row: PayoutRecord) {
    setSelectedId(row.id);
    setSelected(row);
    if (row.agency_id) setAgencyId(row.agency_id);
  }

  async function loadProof(payoutId: string) {
    setProof(await getPlatformPayoutProof(payoutId));
  }

  useEffect(() => {
    if (selectedId) void loadProof(selectedId);
    else setProof(null);
  }, [selectedId]);

  async function runAction(payoutId: string, action: string, transactionRef = "") {
    setBusy(true);
    setMessage("");
    try {
      const updated = await runPlatformPayoutAction(payoutId, {
        action,
        transaction_ref: transactionRef,
      });
      setSelected(updated);
      setSelectedId(updated.id);
      setMessage(
        action === "approve"
          ? "Approved. Next: upload proof, then mark paid."
          : `Payout ${action} completed.`,
      );
      await reload();
    } catch (cause) {
      setMessage(mapPayoutError(cause, "Action failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function markPaid(payoutId: string, transactionRef: string) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await markPlatformPayoutPaid(payoutId, transactionRef);
      setSelected(updated);
      setMessage("Marked paid. Agency receipt is ready.");
      await reload();
    } catch (cause) {
      setMessage(mapPayoutError(cause, "Mark paid failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function uploadProof(payoutId: string, file: File, agencyVisible: boolean) {
    setBusy(true);
    setMessage("");
    try {
      const created = await uploadPlatformPayoutProof(payoutId, file, agencyVisible);
      setProof(created);
      setMessage(
        agencyVisible
          ? "Proof uploaded and shared with this agency."
          : "Proof uploaded (private). Toggle share if the agency should see it.",
      );
    } catch (cause) {
      setMessage(mapPayoutError(cause, "Proof upload failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function setProofAgencyVisible(payoutId: string, agencyVisible: boolean) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await setPlatformPayoutProofAgencyVisible(payoutId, agencyVisible);
      setProof(updated);
      setMessage(
        agencyVisible
          ? "Proof shared with this agency for this payout only."
          : "Proof hidden from the agency again.",
      );
    } catch (cause) {
      setMessage(mapPayoutError(cause, "Could not update proof visibility."));
      throw cause;
    } finally {
      setBusy(false);
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
      await adjustAgencyWallet(input);
      setMessage("Audited wallet adjustment recorded.");
      await loadWallet(input.agencyId);
    } catch (cause) {
      setMessage(mapPayoutError(cause, "Adjustment failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function freezeWallet(input: { agencyId: string; frozen: boolean; reason: string }) {
    setBusy(true);
    setMessage("");
    try {
      await freezeAgencyWallet(input);
      setMessage(input.frozen ? "Wallet frozen." : "Wallet unfrozen.");
      await loadWallet(input.agencyId);
    } catch (cause) {
      setMessage(mapPayoutError(cause, "Freeze failed."));
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    payouts: filtered,
    agencies,
    agencyLabel,
    selected,
    selectedId,
    selectPayout,
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
    setProofAgencyVisible,
    adjustWallet,
    freezeWallet,
  };
}
