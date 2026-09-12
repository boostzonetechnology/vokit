export type KnowledgeRecord = {
  id: string;
  title?: string;
  scope?: string;
  kind?: string;
  status?: string;
};

export const KNOWLEDGE_KINDS = [
  { value: "text", label: "Text" },
  { value: "qa", label: "Q&A" },
  { value: "file", label: "File (extracted text)" },
  { value: "url", label: "URL (extracted text)" },
  { value: "structured", label: "Structured" },
] as const;

export const KNOWLEDGE_STATUSES = [
  "uploaded",
  "processing",
  "ready",
  "failed",
  "stale",
] as const;
