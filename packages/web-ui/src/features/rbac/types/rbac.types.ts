export type RbacNamespace = "platform" | "agency" | "customer";

export type PermissionRecord = {
  id: string;
  namespace: RbacNamespace | string;
  code: string;
  description: string;
  is_sensitive: boolean;
  is_custom: boolean;
};

export type RoleRecord = {
  id: string;
  namespace: RbacNamespace | string;
  slug: string;
  display_name: string;
  is_system: boolean;
  permissions?: string[];
};

export type PermissionSyncResult = {
  synced: boolean;
  permission_count: number;
  role_count: number;
};
