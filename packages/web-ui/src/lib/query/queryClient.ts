import { QueryClient } from "@tanstack/react-query";

const FIVE_MINUTES_MS = 5 * 60 * 1000;

export function createAppQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        gcTime: FIVE_MINUTES_MS,
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  });
}
