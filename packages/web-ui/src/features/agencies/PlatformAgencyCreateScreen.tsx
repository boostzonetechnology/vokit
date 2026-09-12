import { FormEvent, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormSelect } from "@/components/forms/FormSelect";
import { FormStepNav } from "@/components/forms/FormStepNav";
import { PasswordInput } from "@/components/forms/PasswordInput";
import { useCreatePlatformAgency } from "@/features/agencies/hooks/useCreatePlatformAgency";
import { agenciesListHref, agencyDetailHref } from "@/features/agencies/lib/routes";
import {
  CAPABILITY_FIELDS,
  defaultCapabilities,
  type AgencyCapabilities,
} from "@/features/agencies/types";

const STEPS = [
  { id: "agency", label: "Agency" },
  { id: "commercial", label: "Commercial" },
  { id: "database", label: "Database" },
] as const;

type StepId = (typeof STEPS)[number]["id"];

type FormState = {
  display_name: string;
  legal_name: string;
  owner_email: string;
  commission_rate_bps: string;
  currency: string;
  db_username: string;
  db_password: string;
  db_host: string;
  db_port: string;
};

const INITIAL: FormState = {
  display_name: "",
  legal_name: "",
  owner_email: "",
  commission_rate_bps: "1500",
  currency: "USD",
  db_username: "",
  db_password: "",
  db_host: "",
  db_port: "",
};

export function PlatformAgencyCreateScreen() {
  const navigate = useNavigate();
  const { createAgency, error, busy, setError } = useCreatePlatformAgency();
  const [step, setStep] = useState<StepId>("agency");
  const [form, setForm] = useState<FormState>(INITIAL);
  const [capabilities, setCapabilities] = useState<AgencyCapabilities>(defaultCapabilities());
  const [localError, setLocalError] = useState("");

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function validateStep(current: StepId): string {
    if (current === "agency") {
      if (!form.display_name.trim()) return "Display name is required.";
      if (!form.legal_name.trim()) return "Legal name is required.";
      if (!form.owner_email.trim()) return "Owner email is required.";
      return "";
    }
    if (current === "commercial") {
      const bps = Number(form.commission_rate_bps);
      if (!Number.isFinite(bps) || bps < 0) return "Commission must be a valid number.";
      if (!form.currency) return "Currency is required.";
      return "";
    }
    if (!form.db_username.trim()) return "MySQL username is required.";
    if (form.db_password.length < 12) return "MySQL password must be at least 12 characters.";
    if (form.db_port && Number.isNaN(Number(form.db_port))) return "Port must be a number.";
    return "";
  }

  function goNext() {
    const message = validateStep(step);
    if (message) {
      setLocalError(message);
      return;
    }
    setLocalError("");
    setError("");
    const index = STEPS.findIndex((item) => item.id === step);
    const next = STEPS[index + 1];
    if (next) setStep(next.id);
  }

  function goBack() {
    setLocalError("");
    const index = STEPS.findIndex((item) => item.id === step);
    const prev = STEPS[index - 1];
    if (prev) setStep(prev.id);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (step !== "database") {
      goNext();
      return;
    }

    const message = validateStep("database");
    if (message) {
      setLocalError(message);
      return;
    }

    setLocalError("");
    setError("");
    const host = form.db_host.trim();
    const portRaw = form.db_port.trim();
    const port = portRaw ? Number(portRaw) : undefined;

    try {
      const created = await createAgency({
        display_name: form.display_name.trim(),
        legal_name: form.legal_name.trim(),
        owner_email: form.owner_email.trim(),
        commission_rate_bps: Number(form.commission_rate_bps || 0),
        currency: form.currency || "USD",
        capabilities,
        database: {
          username: form.db_username.trim(),
          password: form.db_password,
          host: host || undefined,
          port,
        },
      });
      navigate(agencyDetailHref(created.id));
    } catch {
      /* error shown from hook */
    }
  }

  const alert = localError || error;

  return (
    <section className="mx-auto max-w-[720px]">
      <div className="mb-8">
        <Link
          to={agenciesListHref()}
          className="mb-4 inline-flex items-center gap-2 text-body font-semibold text-text-secondary no-underline hover:text-text-primary"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Agencies
        </Link>
        <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
          Create agency
        </h1>
      </div>

      <div className="mb-6">
        <FormStepNav
          steps={[...STEPS]}
          current={step}
          onChange={(id) => {
            setLocalError("");
            setStep(id as StepId);
          }}
        />
      </div>

      {alert ? (
        <p className="mb-4 text-danger" role="alert">
          {alert}
        </p>
      ) : null}

      <form className="grid gap-6" onSubmit={(event) => void onSubmit(event)} noValidate>
        {step === "agency" ? (
          <div className="grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                label="Display name"
                name="display_name"
                required
                value={form.display_name}
                onChange={(event) => update("display_name", event.target.value)}
              />
              <FormField
                label="Legal name"
                name="legal_name"
                required
                value={form.legal_name}
                onChange={(event) => update("legal_name", event.target.value)}
              />
            </div>
            <FormField
              label="Owner email"
              name="owner_email"
              type="email"
              required
              autoComplete="off"
              value={form.owner_email}
              onChange={(event) => update("owner_email", event.target.value)}
            />
          </div>
        ) : null}

        {step === "commercial" ? (
          <div className="grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                label="Commission (bps)"
                name="commission_rate_bps"
                type="number"
                required
                min={0}
                value={form.commission_rate_bps}
                onChange={(event) => update("commission_rate_bps", event.target.value)}
              />
              <FormSelect
                label="Currency"
                name="currency"
                required
                value={form.currency}
                onChange={(event) => update("currency", event.target.value)}
              >
                <option value="USD">USD</option>
              </FormSelect>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {CAPABILITY_FIELDS.map((field) => {
                const on = capabilities[field.key];
                return (
                  <button
                    key={field.key}
                    type="button"
                    aria-pressed={on}
                    onClick={() =>
                      setCapabilities((prev) => ({
                        ...prev,
                        [field.key]: !prev[field.key],
                      }))
                    }
                    className={
                      on
                        ? "rounded-full border border-brand bg-brand-subtle px-4 py-3 text-left text-body font-semibold text-text-brand"
                        : "rounded-full border border-border-default bg-surface px-4 py-3 text-left text-body font-medium text-text-secondary"
                    }
                  >
                    {field.label}
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}

        {step === "database" ? (
          <div className="grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                label="MySQL username"
                name="db_username"
                required
                autoComplete="off"
                value={form.db_username}
                onChange={(event) => update("db_username", event.target.value)}
              />
              <PasswordInput
                label="MySQL password"
                name="db_password"
                required
                minLength={12}
                value={form.db_password}
                onChange={(value) => update("db_password", value)}
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                label="Host"
                name="db_host"
                autoComplete="off"
                placeholder="Optional"
                value={form.db_host}
                onChange={(event) => update("db_host", event.target.value)}
              />
              <FormField
                label="Port"
                name="db_port"
                type="number"
                autoComplete="off"
                placeholder="Optional"
                value={form.db_port}
                onChange={(event) => update("db_port", event.target.value)}
              />
            </div>
          </div>
        ) : null}

        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <ActionButton type="button" variant="outline" disabled={busy || step === "agency"} onClick={goBack}>
            Back
          </ActionButton>
          <div className="flex flex-wrap gap-2">
            <ActionButton
              type="button"
              variant="outline"
              disabled={busy}
              onClick={() => navigate(agenciesListHref())}
            >
              Cancel
            </ActionButton>
            {step === "database" ? (
              <ActionButton type="submit" disabled={busy}>
                {busy ? "Creating…" : "Create agency"}
              </ActionButton>
            ) : (
              <ActionButton type="submit">Continue</ActionButton>
            )}
          </div>
        </div>
      </form>
    </section>
  );
}
