import { StatusBadge } from "@/components/ui/StatusBadge";
import { disabledCapabilityLabels } from "@/features/agencies/lib/gates";
import type { AgencyCapabilities } from "@/features/agencies/types";

/** Compact chip row of currently blocked capability gates (platform detail header). */
export function AgencyGateChips({
  capabilities,
}: {
  capabilities?: AgencyCapabilities | null;
}) {
  const blocked = disabledCapabilityLabels(capabilities);
  if (blocked.length === 0) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-2" aria-label="Blocked capability gates">
      {blocked.map((label) => (
        <StatusBadge key={label} tone="warning">
          {`${label} off`}
        </StatusBadge>
      ))}
    </div>
  );
}
