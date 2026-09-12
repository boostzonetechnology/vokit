import { useCallback, useEffect, useState } from "react";

import { apiGet, apiSend, isApiError } from "@/api";
import type { KycCase } from "@/features/kyc/types";

export type AgencyKycStatus = {
  status?: string;
  payout_eligible?: boolean;
  payout_block_reason?: string | null;
  next_step?: string;
  case?: KycCase | null;
};

export type KycSessionStart = {
  hosted_url?: string;
  session_id?: string;
  status?: string;
};

export function useAgencyKyc() {
  const [status, setStatus] = useState<AgencyKycStatus | null>(null);
  const [session, setSession] = useState<KycSessionStart | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiGet<AgencyKycStatus>("/api/v1/agency/kyc");
      setStatus(data);
      setError("");
    } catch (cause) {
      setError(isApiError(cause) ? cause.message : "Failed to load KYC status.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function startSession() {
    setBusy(true);
    setMessage("");
    try {
      const started = await apiSend<KycSessionStart>("/api/v1/agency/kyc/session", "POST", {});
      setSession(started);
      setMessage(
        started.hosted_url
          ? "KYC session ready — complete verification in the hosted flow."
          : "KYC session started.",
      );
      await reload();
      return started;
    } catch (cause) {
      setMessage(isApiError(cause) ? cause.message : "Could not start KYC session.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  return {
    status,
    session,
    error,
    message,
    loading,
    busy,
    reload,
    startSession,
  };
}
