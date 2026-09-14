import { createContext, useContext, type ReactNode } from "react";

import type { SessionPayload } from "@/api";

const SessionContext = createContext<SessionPayload | null>(null);

export function SessionProvider({
  session,
  children,
}: {
  session: SessionPayload;
  children: ReactNode;
}) {
  return <SessionContext.Provider value={session}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionPayload {
  const session = useContext(SessionContext);
  if (!session) {
    throw new Error("useSession must be used within SessionProvider.");
  }
  return session;
}

export function useSessionOptional(): SessionPayload | null {
  return useContext(SessionContext);
}
