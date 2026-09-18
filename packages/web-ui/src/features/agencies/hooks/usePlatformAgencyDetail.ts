import { useCallback, useEffect, useState } from "react";

import { mapAgencyError } from "@/features/agencies/lib/mapAgencyError";
import {
  createAgencyNote,
  getAgency,
  getAgencyFinance,
  listAgencyNotes,
  listAgencyScopedRows,
  patchAgencyProfile,
  setAgencyCapabilities,
  setAgencyCommission,
  setAgencyStatus,
} from "@/features/agencies/services/agency.service";
import type {
  AgencyCapabilities,
  AgencyFinance,
  AgencyNote,
  AgencyRecord,
  SetCommissionInput,
  SetStatusInput,
} from "@/features/agencies/types";

async function safeScoped(
  path: string,
  agencyId: string,
): Promise<Record<string, unknown>[]> {
  try {
    return await listAgencyScopedRows(path, agencyId);
  } catch {
    return [];
  }
}

export function usePlatformAgencyDetail(agencyId: string) {
  const [detail, setDetail] = useState<AgencyRecord | null>(null);
  const [finance, setFinance] = useState<AgencyFinance | null>(null);
  const [customers, setCustomers] = useState<Record<string, unknown>[]>([]);
  const [agents, setAgents] = useState<Record<string, unknown>[]>([]);
  const [numbers, setNumbers] = useState<Record<string, unknown>[]>([]);
  const [calls, setCalls] = useState<Record<string, unknown>[]>([]);
  const [integrations, setIntegrations] = useState<Record<string, unknown>[]>([]);
  const [team, setTeam] = useState<Record<string, unknown>[]>([]);
  const [knowledge, setKnowledge] = useState<Record<string, unknown>[]>([]);
  const [notes, setNotes] = useState<AgencyNote[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const loadDetail = useCallback(async (id: string) => {
    if (!id) {
      setDetail(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const agency = await getAgency(id);
      setDetail(agency);

      const [
        financeRes,
        customerRows,
        agentRows,
        numberRows,
        callRows,
        integrationRows,
        teamRows,
        knowledgeRows,
        noteRows,
      ] = await Promise.all([
        getAgencyFinance(id).catch(() => null),
        safeScoped("/api/v1/platform/customers", id),
        safeScoped("/api/v1/platform/agents", id),
        safeScoped("/api/v1/platform/phone-numbers", id),
        safeScoped("/api/v1/platform/calls", id),
        safeScoped("/api/v1/platform/integrations", id),
        safeScoped("/api/v1/platform/users", id),
        safeScoped("/api/v1/platform/knowledge", id),
        listAgencyNotes(id).catch(() => [] as AgencyNote[]),
      ]);

      setFinance(financeRes);
      setCustomers(customerRows);
      setAgents(agentRows);
      setNumbers(numberRows);
      setCalls(callRows);
      setIntegrations(integrationRows);
      setTeam(teamRows);
      setKnowledge(knowledgeRows);
      setNotes(noteRows);
    } catch (cause) {
      setDetail(null);
      setError(mapAgencyError(cause, "Failed to load agency detail."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDetail(agencyId);
  }, [agencyId, loadDetail]);

  async function saveProfile(input: { display_name: string; legal_name: string }) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await patchAgencyProfile(agencyId, input);
      setDetail(updated);
      setMessage("Agency profile updated.");
    } catch (cause) {
      setMessage(mapAgencyError(cause, "Profile update failed."));
    } finally {
      setBusy(false);
    }
  }

  async function setCommission(input: SetCommissionInput) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await setAgencyCommission(agencyId, input);
      setDetail(updated);
      const financeRes = await getAgencyFinance(agencyId).catch(() => null);
      if (financeRes) setFinance(financeRes);
      setMessage("Commission rate updated. Historical ledger entries keep their snapshot.");
    } catch (cause) {
      setMessage(mapAgencyError(cause, "Commission update failed."));
    } finally {
      setBusy(false);
    }
  }

  async function setStatus(input: Omit<SetStatusInput, "confirm"> & { confirm?: true }) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await setAgencyStatus(agencyId, {
        action: input.action,
        confirm: true,
        reason: input.reason,
      });
      setDetail(updated);
      setMessage(`Status updated: ${input.action.replaceAll("_", " ")}`);
    } catch (cause) {
      setMessage(mapAgencyError(cause, "Status update failed."));
    } finally {
      setBusy(false);
    }
  }

  async function setCapabilities(input: {
    capabilities: AgencyCapabilities;
    reason: string;
  }) {
    setBusy(true);
    setMessage("");
    try {
      const updated = await setAgencyCapabilities(agencyId, {
        confirm: true,
        reason: input.reason,
        capabilities: input.capabilities,
      });
      setDetail(updated);
      setMessage("Capabilities updated.");
    } catch (cause) {
      setMessage(mapAgencyError(cause, "Capabilities update failed."));
    } finally {
      setBusy(false);
    }
  }

  async function addNote(input: { body: string; risk_flag: boolean }) {
    setBusy(true);
    setMessage("");
    try {
      const created = await createAgencyNote(agencyId, input);
      setNotes((prev) => [created, ...prev]);
      setMessage("Internal note added.");
    } catch (cause) {
      setMessage(mapAgencyError(cause, "Could not add note."));
    } finally {
      setBusy(false);
    }
  }

  return {
    detail,
    finance,
    customers,
    agents,
    numbers,
    calls,
    integrations,
    team,
    knowledge,
    notes,
    error,
    message,
    loading,
    busy,
    saveProfile,
    setCommission,
    setStatus,
    setCapabilities,
    addNote,
  };
}
