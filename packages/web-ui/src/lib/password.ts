/** Cryptographically strong password for tenant MySQL credentials. */
export function generateSecurePassword(length = 20): string {
  const upper = "ABCDEFGHJKLMNPQRSTUVWXYZ";
  const lower = "abcdefghijkmnopqrstuvwxyz";
  const digits = "23456789";
  const symbols = "!@#$%^&*-_=+";
  const pools = [upper, lower, digits, symbols];
  const all = pools.join("");

  const pick = (alphabet: string) => {
    const bytes = new Uint8Array(1);
    crypto.getRandomValues(bytes);
    return alphabet[bytes[0] % alphabet.length];
  };

  const chars: string[] = pools.map((pool) => pick(pool));
  const rest = new Uint8Array(Math.max(length - chars.length, 0));
  crypto.getRandomValues(rest);
  for (const byte of rest) {
    chars.push(all[byte % all.length]);
  }

  for (let i = chars.length - 1; i > 0; i -= 1) {
    const bytes = new Uint8Array(1);
    crypto.getRandomValues(bytes);
    const j = bytes[0] % (i + 1);
    [chars[i], chars[j]] = [chars[j], chars[i]];
  }

  return chars.join("");
}
