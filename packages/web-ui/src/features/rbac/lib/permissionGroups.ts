import type { PermissionRecord } from "@/features/rbac/types/rbac.types";

/** Group permission codes by module prefix (before first `.`). */
export function groupPermissionsByModule(
  permissions: PermissionRecord[],
): Array<{ module: string; items: PermissionRecord[] }> {
  const map = new Map<string, PermissionRecord[]>();
  for (const item of permissions) {
    const module = item.code.includes(".") ? item.code.split(".")[0]! : item.code;
    const bucket = map.get(module) ?? [];
    bucket.push(item);
    map.set(module, bucket);
  }
  return Array.from(map.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([module, items]) => ({
      module,
      items: items.slice().sort((a, b) => a.code.localeCompare(b.code)),
    }));
}
