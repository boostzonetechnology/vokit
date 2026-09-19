export function PlanTermsFields({
  availableIntegrations,
}: {
  availableIntegrations?: string[];
}) {
  const hint =
    availableIntegrations && availableIntegrations.length > 0
      ? `Known providers: ${availableIntegrations.join(", ")}. Leave empty for all.`
      : "Comma or newline separated provider slugs. Leave empty for all providers.";

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <Field label="Price (minor)" name="price_minor" defaultValue="10000" />
      <Field label="Included minutes" name="included_minutes" defaultValue="100" />
      <Field label="Top-up minutes" name="topup_minutes" defaultValue="50" />
      <Field label="Top-up price (minor)" name="topup_price_minor" defaultValue="2000" />
      <Field
        label="Overage price / min (minor)"
        name="overage_price_per_minute_minor"
        defaultValue="0"
      />
      <Field label="Grace seconds" name="grace_seconds" defaultValue="30" />
      <Field
        label="Max agents (0 = unlimited)"
        name="max_agents"
        defaultValue="0"
        hint="Active agents only count against this cap."
      />
      <Field
        label="Max phone numbers (0 = unlimited)"
        name="max_phone_numbers"
        defaultValue="0"
      />
      <Field
        label="Max concurrency (0 = unlimited)"
        name="max_concurrency"
        defaultValue="0"
        hint="Ringing + in-progress calls."
      />
      <label className="m-0 grid gap-1.5 font-normal sm:col-span-2 xl:col-span-3">
        <span className="text-body-sm text-text-muted">Allowed integrations</span>
        <textarea
          name="allowed_integrations"
          rows={2}
          placeholder="Empty = all providers"
          className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
        />
        <span className="text-body-sm text-text-muted">{hint}</span>
      </label>
      <label className="m-0 flex items-center gap-2 font-normal">
        <input type="checkbox" name="allow_topups" defaultChecked />
        <span className="text-body text-text-secondary">Allow top-ups</span>
      </label>
      <label className="m-0 flex items-center gap-2 font-normal">
        <input type="checkbox" name="overage_enabled" />
        <span className="text-body text-text-secondary">Overage enabled</span>
      </label>
      <label className="m-0 flex items-center gap-2 font-normal">
        <input type="checkbox" name="recording_allowed" defaultChecked />
        <span className="text-body text-text-secondary">Recording allowed</span>
      </label>
    </div>
  );
}

function Field({
  label,
  name,
  defaultValue,
  required,
  hint,
}: {
  label: string;
  name: string;
  defaultValue?: string;
  required?: boolean;
  hint?: string;
}) {
  return (
    <label className="m-0 grid gap-1.5 font-normal">
      <span className="text-body-sm text-text-muted">{label}</span>
      <input
        name={name}
        required={required}
        defaultValue={defaultValue}
        className="rounded-xl border border-border-default bg-surface px-3 py-2.5 text-body"
      />
      {hint ? <span className="text-body-sm text-text-muted">{hint}</span> : null}
    </label>
  );
}
