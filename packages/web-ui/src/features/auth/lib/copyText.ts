/** Best-effort clipboard write; fails silently when unavailable. */
export async function copyTextToClipboard(value: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value);
  } catch {
    // Clipboard may be unavailable; caller UI still allows manual copy.
  }
}
