export function shortId(id?: string | null): string {
  if (!id) return "—";
  return id.length > 8 ? id.slice(0, 8) : id;
}

export function nameOrId(name?: string | null, id?: string | null): string {
  const trimmed = name?.trim();
  if (trimmed) return trimmed;
  return shortId(id);
}

export function formatWhen(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}
