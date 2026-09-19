/** Short opaque id for secondary UI (never primary label when a name exists). */
export function shortId(id?: string | null): string {
  if (!id) return "—";
  return id.length > 8 ? id.slice(0, 8) : id;
}

/** Prefer human name; fall back to short id. */
export function nameOrId(name?: string | null, id?: string | null): string {
  const trimmed = name?.trim();
  if (trimmed) return trimmed;
  return shortId(id);
}
