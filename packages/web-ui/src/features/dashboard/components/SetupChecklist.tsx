import { CheckCircle2, Circle } from "lucide-react";

import type { DashboardPayload } from "../../../api";
import { kpiValue } from "../lib/format";

type Step = { id: string; label: string; done: boolean; href: string };

export function SetupChecklist({
  data,
  onNavigate,
}: {
  data: DashboardPayload;
  onNavigate: (href: string) => void;
}) {
  const agencies = Number(kpiValue(data, "agencies") ?? 0);
  const customers = Number(kpiValue(data, "customers") ?? 0);
  const numbers = Number(kpiValue(data, "numbers") ?? 0);
  const calls = Number(kpiValue(data, "calls") ?? 0);

  const steps: Step[] = [
    {
      id: "agency",
      label: "Create your first agency",
      done: agencies > 0,
      href: "#/agencies",
    },
    {
      id: "number",
      label: "Choose a phone number",
      done: numbers > 0,
      href: "#/numbers",
    },
    {
      id: "customer",
      label: "Add your first customer",
      done: customers > 0,
      href: "#/customers",
    },
    {
      id: "call",
      label: "Place a test call",
      done: calls > 0,
      href: "#/calls",
    },
  ];

  const next = steps.find((step) => !step.done) ?? steps[steps.length - 1]!;

  return (
    <article className="flex h-full flex-col rounded-xl border border-border-default bg-surface p-5 shadow-subtle">
      <h3 className="m-0 text-section text-text-primary">Setup checklist</h3>
      <ul className="mt-4 m-0 flex-1 list-none space-y-3 p-0">
        {steps.map((step) => (
          <li key={step.id}>
            <button
              type="button"
              className="flex w-full items-center gap-2.5 bg-transparent p-0 text-left text-body text-text-primary"
              onClick={() => onNavigate(step.href)}
            >
              {step.done ? (
                <CheckCircle2 className="size-5 shrink-0 text-success" aria-hidden />
              ) : (
                <Circle className="size-5 shrink-0 text-border-strong" aria-hidden />
              )}
              <span className={step.done ? "text-text-secondary line-through" : ""}>
                {step.label}
              </span>
            </button>
          </li>
        ))}
      </ul>
      <button
        type="button"
        className="mt-4 w-full rounded-lg bg-brand py-2.5 text-body font-semibold text-text-inverse"
        onClick={() => onNavigate(next.href)}
      >
        Continue setup →
      </button>
    </article>
  );
}
