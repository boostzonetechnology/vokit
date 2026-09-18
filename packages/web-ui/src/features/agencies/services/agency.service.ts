import { apiGet, apiSend } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type {
  AgencyCapabilities,
  AgencyFinance,
  AgencyNote,
  AgencyRecord,
  CreateAgencyInput,
  SetCapabilitiesInput,
  SetCommissionInput,
  SetStatusInput,
} from "@/features/agencies/types";

function withAgencyId(path: string, agencyId: string): string {
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}agency_id=${encodeURIComponent(agencyId)}`;
}

export async function listAgencies(filters: {
  status?: string;
  name?: string;
}): Promise<AgencyRecord[]> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.name) params.set("name", filters.name);
  const query = params.toString();
  const path = query ? `/api/v1/platform/agencies?${query}` : "/api/v1/platform/agencies";
  return asList<AgencyRecord>(await apiGet<unknown>(path));
}

export async function getAgency(agencyId: string): Promise<AgencyRecord> {
  return apiGet<AgencyRecord>(`/api/v1/platform/agencies/${agencyId}`);
}

export async function createAgency(input: CreateAgencyInput): Promise<AgencyRecord> {
  const database: Record<string, string | number> = {
    username: input.database.username,
    password: input.database.password,
  };
  if (input.database.host) database.host = input.database.host;
  if (typeof input.database.port === "number" && !Number.isNaN(input.database.port)) {
    database.port = input.database.port;
  }
  return apiSend<AgencyRecord>("/api/v1/platform/agencies", "POST", {
    display_name: input.display_name,
    legal_name: input.legal_name,
    owner_email: input.owner_email,
    commission_rate_bps: input.commission_rate_bps,
    currency: input.currency,
    capabilities: input.capabilities,
    database,
  });
}

export async function patchAgencyProfile(
  agencyId: string,
  input: { display_name: string; legal_name: string },
): Promise<AgencyRecord> {
  return apiSend<AgencyRecord>(`/api/v1/platform/agencies/${agencyId}`, "PATCH", input);
}

export async function setAgencyCommission(
  agencyId: string,
  input: SetCommissionInput,
): Promise<AgencyRecord> {
  const body: Record<string, unknown> = {
    commission_rate_bps: input.commission_rate_bps,
    reason: input.reason,
  };
  if (input.rate_effective_at) {
    body.rate_effective_at = input.rate_effective_at;
  }
  return apiSend<AgencyRecord>(`/api/v1/platform/agencies/${agencyId}/commission`, "POST", body);
}

export async function setAgencyStatus(
  agencyId: string,
  input: SetStatusInput,
): Promise<AgencyRecord> {
  const body: Record<string, unknown> = {
    action: input.action,
    confirm: true,
  };
  if (input.reason) body.reason = input.reason;
  return apiSend<AgencyRecord>(`/api/v1/platform/agencies/${agencyId}/status`, "POST", body);
}

export async function setAgencyCapabilities(
  agencyId: string,
  input: SetCapabilitiesInput,
): Promise<AgencyRecord> {
  return apiSend<AgencyRecord>(`/api/v1/platform/agencies/${agencyId}/capabilities`, "POST", {
    confirm: true,
    reason: input.reason,
    capabilities: input.capabilities,
  });
}

export async function getAgencyFinance(agencyId: string): Promise<AgencyFinance> {
  return apiGet<AgencyFinance>(`/api/v1/platform/agencies/${agencyId}/finance`);
}

export async function listAgencyNotes(agencyId: string): Promise<AgencyNote[]> {
  return asList<AgencyNote>(
    await apiGet<unknown>(`/api/v1/platform/agencies/${agencyId}/notes`),
  );
}

export async function createAgencyNote(
  agencyId: string,
  input: { body: string; risk_flag: boolean },
): Promise<AgencyNote> {
  return apiSend<AgencyNote>(`/api/v1/platform/agencies/${agencyId}/notes`, "POST", input);
}

export async function listAgencyScopedRows(
  collectionPath: string,
  agencyId: string,
): Promise<Record<string, unknown>[]> {
  return asList<Record<string, unknown>>(
    await apiGet<unknown>(withAgencyId(collectionPath, agencyId)),
  );
}
