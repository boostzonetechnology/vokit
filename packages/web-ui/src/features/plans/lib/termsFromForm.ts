import type { PlanTermsInput } from "@/features/plans/types";

export function termsFromForm(form: FormData): PlanTermsInput {
  const integrationsRaw = String(form.get("allowed_integrations") || "").trim();
  const allowed_integrations = integrationsRaw
    ? integrationsRaw
        .split(/[\n,]/)
        .map((item) => item.trim())
        .filter(Boolean)
    : [];

  return {
    price_minor: Number(form.get("price_minor") || 0),
    included_minutes: Number(form.get("included_minutes") || 0),
    allow_topups: form.get("allow_topups") === "on",
    topup_minutes: Number(form.get("topup_minutes") || 0),
    topup_price_minor: Number(form.get("topup_price_minor") || 0),
    overage_enabled: form.get("overage_enabled") === "on",
    overage_price_per_minute_minor: Number(form.get("overage_price_per_minute_minor") || 0),
    grace_seconds: Number(form.get("grace_seconds") || 0),
    max_agents: Number(form.get("max_agents") || 0),
    max_phone_numbers: Number(form.get("max_phone_numbers") || 0),
    max_concurrency: Number(form.get("max_concurrency") || 0),
    recording_allowed: form.get("recording_allowed") === "on",
    allowed_integrations,
  };
}
