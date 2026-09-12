export type GlobalInstructionsPayload = {
  body?: string;
};

/** Documented inheritance order from agents README — not configurable via API. */
export const INSTRUCTION_PRECEDENCE = [
  {
    layer: "Platform safety",
    source: "Global instructions",
    rule: "Always applied; cannot be overridden by lower layers.",
  },
  {
    layer: "Template",
    source: "Template version instructions",
    rule: "Applied when an agent is created from a template.",
  },
  {
    layer: "Agency",
    source: "Agency-scoped instructions",
    rule: "Agency defaults for customer agents when configured.",
  },
  {
    layer: "Customer",
    source: "Customer-scoped instructions",
    rule: "Customer overrides within agency policy.",
  },
  {
    layer: "Agent",
    source: "Agent-specific instructions",
    rule: "Most specific operational instructions for the live agent.",
  },
] as const;
