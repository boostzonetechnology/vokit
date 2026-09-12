import { cn } from "@/lib/utils";

export type FormStep = {
  id: string;
  label: string;
};

export function FormStepNav({
  steps,
  current,
  onChange,
}: {
  steps: FormStep[];
  current: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Form steps">
      {steps.map((step, index) => {
        const active = step.id === current;
        return (
          <button
            key={step.id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(step.id)}
            className={cn(
              "inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-body font-semibold transition-colors",
              active
                ? "bg-brand text-text-inverse shadow-subtle"
                : "border border-border-default bg-surface text-text-muted hover:text-text-secondary",
            )}
          >
            <span
              className={cn(
                "inline-flex size-6 items-center justify-center rounded-full text-body-sm",
                active ? "bg-white/20 text-text-inverse" : "bg-canvas text-text-muted",
              )}
              aria-hidden
            >
              {index + 1}
            </span>
            {step.label}
          </button>
        );
      })}
    </div>
  );
}
