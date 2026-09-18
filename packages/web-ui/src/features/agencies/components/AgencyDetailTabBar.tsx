import type { AgencyDetailTab } from "@/features/agencies/types";

const TABS: Array<{ id: AgencyDetailTab; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "profile", label: "Profile" },
  { id: "commission", label: "Commission" },
  { id: "status", label: "Status" },
  { id: "capabilities", label: "Capabilities" },
  { id: "financial", label: "Financial" },
  { id: "resources", label: "Resources" },
  { id: "notes", label: "Notes" },
];

export function AgencyDetailTabBar({
  tab,
  onChange,
}: {
  tab: AgencyDetailTab;
  onChange: (tab: AgencyDetailTab) => void;
}) {
  return (
    <div className="mb-4 flex flex-wrap gap-2" role="tablist" aria-label="Agency sections">
      {TABS.map((item) => (
        <button
          key={item.id}
          type="button"
          role="tab"
          aria-selected={tab === item.id}
          className={
            tab === item.id
              ? "rounded-xl bg-brand px-3.5 py-2 text-body font-semibold text-text-inverse"
              : "rounded-xl border border-border-default bg-canvas px-3.5 py-2 text-body font-semibold text-text-secondary hover:border-brand/40"
          }
          onClick={() => onChange(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
