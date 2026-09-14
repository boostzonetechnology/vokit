import { apiGet, apiSend } from "@/api";
import { asList } from "@/features/platform/lib/list";
import type {
  PermissionRecord,
  PermissionSyncResult,
  RoleRecord,
  RbacNamespace,
} from "@/features/rbac/types/rbac.types";

export async function listPlatformPermissions(params?: {
  namespace?: string;
  module?: string;
}): Promise<PermissionRecord[]> {
  const query = new URLSearchParams();
  if (params?.namespace) query.set("namespace", params.namespace);
  if (params?.module) query.set("module", params.module);
  const qs = query.toString();
  const path = `/api/v1/platform/permissions${qs ? `?${qs}` : ""}`;
  return asList<PermissionRecord>(await apiGet<unknown>(path));
}

export async function createPlatformPermission(input: {
  namespace: string;
  code: string;
  description?: string;
  is_sensitive?: boolean;
}): Promise<PermissionRecord> {
  return apiSend<PermissionRecord>("/api/v1/platform/permissions", "POST", {
    namespace: input.namespace,
    code: input.code,
    description: input.description ?? "",
    is_sensitive: Boolean(input.is_sensitive),
  });
}

export async function syncPlatformPermissions(): Promise<PermissionSyncResult> {
  return apiSend<PermissionSyncResult>("/api/v1/platform/permissions/sync", "POST", {});
}

export async function listPlatformRoles(namespace?: string): Promise<RoleRecord[]> {
  const qs = namespace ? `?namespace=${encodeURIComponent(namespace)}` : "";
  return asList<RoleRecord>(await apiGet<unknown>(`/api/v1/platform/roles${qs}`));
}

export async function getPlatformRole(roleId: string): Promise<RoleRecord> {
  return apiGet<RoleRecord>(`/api/v1/platform/roles/${roleId}`);
}

export async function createPlatformRole(input: {
  slug: string;
  display_name?: string;
  namespace?: string;
  permissions?: string[];
}): Promise<RoleRecord> {
  return apiSend<RoleRecord>("/api/v1/platform/roles", "POST", {
    slug: input.slug,
    display_name: input.display_name ?? input.slug,
    namespace: input.namespace ?? "platform",
    permissions: input.permissions ?? [],
  });
}

export async function updatePlatformRole(
  roleId: string,
  input: { display_name?: string; permissions?: string[] },
): Promise<RoleRecord> {
  return apiSend<RoleRecord>(`/api/v1/platform/roles/${roleId}`, "PATCH", {
    ...(input.display_name !== undefined ? { display_name: input.display_name } : {}),
    ...(input.permissions !== undefined ? { permissions: input.permissions } : {}),
  });
}

export async function deletePlatformRole(roleId: string): Promise<{ deleted: boolean }> {
  return apiSend<{ deleted: boolean }>(`/api/v1/platform/roles/${roleId}`, "DELETE");
}

export async function listAgencyRoles(): Promise<RoleRecord[]> {
  return asList<RoleRecord>(await apiGet<unknown>("/api/v1/agency/roles"));
}

export async function listCustomerRoles(): Promise<RoleRecord[]> {
  return asList<RoleRecord>(await apiGet<unknown>("/api/v1/customer/roles"));
}

export async function listPortalRoles(
  portal: Exclude<RbacNamespace, never> | "platform" | "agency" | "customer",
  namespace?: string,
): Promise<RoleRecord[]> {
  if (portal === "agency") return listAgencyRoles();
  if (portal === "customer") return listCustomerRoles();
  return listPlatformRoles(namespace);
}
