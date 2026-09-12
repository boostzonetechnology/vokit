import { FormEvent, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { ActionButton } from "@/components/ui/ActionButton";
import { FormField } from "@/components/forms/FormField";
import { FormStepNav } from "@/components/forms/FormStepNav";
import { useCreateAgencyCustomer } from "@/features/customers/hooks/useCreateAgencyCustomer";
import { customersListHref, customerDetailHref } from "@/features/customers/lib/routes";
import { ApiNote } from "@/features/platform/ux/ApiNote";

const STEPS = [
  { id: "account", label: "Account" },
  { id: "profile", label: "Profile" },
] as const;

type StepId = (typeof STEPS)[number]["id"];

type FormState = {
  display_name: string;
  owner_email: string;
  legal_name: string;
  phone: string;
  country: string;
  timezone: string;
};

const INITIAL: FormState = {
  display_name: "",
  owner_email: "",
  legal_name: "",
  phone: "",
  country: "",
  timezone: "",
};

export function AgencyCustomerCreateScreen() {
  const navigate = useNavigate();
  const { createCustomer, error, busy, setError } = useCreateAgencyCustomer();
  const [step, setStep] = useState<StepId>("account");
  const [form, setForm] = useState<FormState>(INITIAL);
  const [localError, setLocalError] = useState("");

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function validateStep(current: StepId): string {
    if (current === "account") {
      if (!form.display_name.trim()) return "Display name is required.";
      if (!form.owner_email.trim()) return "Owner email is required.";
      return "";
    }
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
    if (step !== "profile") {
      goNext();
      return;
    }

    const message = validateStep("account");
    if (message) {
      setLocalError(message);
      setStep("account");
      return;
    }

    setLocalError("");
    setError("");
    try {
      const created = await createCustomer({
        display_name: form.display_name.trim(),
        owner_email: form.owner_email.trim(),
        legal_name: form.legal_name.trim() || undefined,
        phone: form.phone.trim() || undefined,
        country: form.country.trim() || undefined,
        timezone: form.timezone.trim() || undefined,
      });
      navigate(customerDetailHref(created.id));
    } catch {
      /* hook error */
    }
  }

  const alert = localError || error;

  return (
    <section className="mx-auto max-w-[720px]">
      <div className="mb-8">
        <Link
          to={customersListHref()}
          className="mb-4 inline-flex items-center gap-2 text-body font-semibold text-text-secondary no-underline hover:text-text-primary"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Customers
        </Link>
        <h1 className="m-0 text-[1.85rem] font-bold tracking-[-0.02em] text-text-primary">
          Create customer
        </h1>
        <p className="mt-1 mb-0 text-body text-text-muted">
          Creates an invited customer and sends the owner invite (AG2-001 / AG2-002).
        </p>
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

      <div className="mb-4">
        <ApiNote>
          Create requires agency Active + create_customers capability. Server enforces this; the UI
          cannot override.
        </ApiNote>
      </div>

      {alert ? (
        <p className="mb-4 text-danger" role="alert">
          {alert}
        </p>
      ) : null}

      <form className="grid gap-6" onSubmit={(event) => void onSubmit(event)} noValidate>
        {step === "account" ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="Display name"
              name="display_name"
              required
              value={form.display_name}
              onChange={(event) => update("display_name", event.target.value)}
            />
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

        {step === "profile" ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="Legal name"
              name="legal_name"
              value={form.legal_name}
              onChange={(event) => update("legal_name", event.target.value)}
            />
            <FormField
              label="Phone"
              name="phone"
              value={form.phone}
              onChange={(event) => update("phone", event.target.value)}
            />
            <FormField
              label="Country"
              name="country"
              value={form.country}
              onChange={(event) => update("country", event.target.value)}
            />
            <FormField
              label="Timezone"
              name="timezone"
              placeholder="e.g. UTC"
              value={form.timezone}
              onChange={(event) => update("timezone", event.target.value)}
            />
          </div>
        ) : null}

        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <ActionButton type="button" variant="outline" disabled={busy || step === "account"} onClick={goBack}>
            Back
          </ActionButton>
          <div className="flex flex-wrap gap-2">
            <ActionButton
              type="button"
              variant="outline"
              disabled={busy}
              onClick={() => navigate(customersListHref())}
            >
              Cancel
            </ActionButton>
            {step === "profile" ? (
              <ActionButton type="submit" disabled={busy}>
                {busy ? "Creating…" : "Create customer"}
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
