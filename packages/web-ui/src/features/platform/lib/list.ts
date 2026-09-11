export function asList<T>(data: unknown, keys: string[] = ["results", "items"]): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;
    for (const key of keys) {
      if (Array.isArray(record[key])) return record[key] as T[];
    }
  }
  return [];
}

export async function safeGetList<T>(
  path: string,
  loader: (path: string) => Promise<unknown>,
  keys?: string[],
): Promise<T[]> {
  try {
    return asList<T>(await loader(path), keys);
  } catch {
    return [];
  }
}
