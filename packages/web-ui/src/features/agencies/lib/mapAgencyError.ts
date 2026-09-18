import { isApiError } from "@/api";

export function mapAgencyError(cause: unknown, fallback: string): string {
  if (!isApiError(cause)) {
    return fallback;
  }
  return cause.message || fallback;
}
