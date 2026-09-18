export function AgencyInfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-xl border border-border-default bg-canvas px-3.5 py-3.5">
      <p className="m-0 text-body-sm text-text-muted">{label}</p>
      <p className="mt-1.5 mb-0 break-words font-semibold text-text-primary">{value}</p>
    </div>
  );
}

