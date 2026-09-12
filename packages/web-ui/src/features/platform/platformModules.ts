export type PlatformColumn = { key: string; label: string };

export type PlatformModuleConfig = {
  route: string;
  title: string;
  subtitle: string;
  path: string;
  columns: PlatformColumn[];
  empty: string;
  permissionHint?: string;
  apiGaps?: string[];
  objectMode?: boolean;
};

/** Remaining generic platform module (Risk only — KYC has a custom screen). */
export const PLATFORM_MODULES: Record<string, PlatformModuleConfig> = {
  risk: {
    route: "risk",
    title: "Risk",
    subtitle: "Payment risk and chargeback cases",
    path: "/api/v1/platform/risk/cases",
    columns: [
      { key: "status", label: "Status" },
      { key: "customer_id", label: "Customer" },
      { key: "tenant_id", label: "Agency" },
      { key: "updated_at", label: "Updated" },
      { key: "id", label: "Case" },
    ],
    empty: "No risk cases.",
    permissionHint: "risk.review",
  },
};

export function cellValue(value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
