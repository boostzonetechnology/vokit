import { useEffect, useMemo, useState } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  Portal,
  SessionPayload,
  getPortalMe,
  isApiError,
  logout,
} from "@/api";
import { AppShell } from "@/components/layout/AppShell";
import { PageContentSkeleton } from "@/components/ui/PageContentSkeleton";
import { LoginScreen } from "@/features/auth/components/LoginScreen";
import { AcceptInviteScreen } from "@/features/auth/components/AcceptInviteScreen";
import { SessionProvider } from "@/features/auth/context/SessionContext";
import { useLoginFlow } from "@/features/auth/hooks/useLoginFlow";
import { HighRiskRouteGate } from "@/features/rbac/components/HighRiskRouteGate";
import { AgencyDashboard } from "@/features/dashboard/AgencyDashboard";
import { CustomerDashboard } from "@/features/dashboard/CustomerDashboard";
import { PlatformDashboard } from "@/features/dashboard/PlatformDashboard";
import { createAppQueryClient } from "@/lib/query/queryClient";
import { portalNav, routeFromPathname, toAppPath } from "@/nav";
import { renderProductScreen } from "@/productScreens";

type View = "loading" | "login" | "home" | "unauthenticated" | "forbidden";

function isAcceptInviteRoute(route: string): boolean {
  return route === "accept-invite" || route.startsWith("accept-invite?");
}

function isLoginRoute(route: string): boolean {
  return route === "login";
}

function isPublicAuthRoute(route: string): boolean {
  return isLoginRoute(route) || isAcceptInviteRoute(route);
}

/** One-time migration for bookmarks that still use hash URLs. */
function LegacyHashRedirect() {
  const navigate = useNavigate();

  useEffect(() => {
    const hash = window.location.hash;
    if (!hash.startsWith("#/")) return;
    navigate(toAppPath(hash), { replace: true });
  }, [navigate]);

  return null;
}

export function PortalApp({ portal, title }: { portal: Portal; title: string }) {
  const [queryClient] = useState(() => createAppQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <LegacyHashRedirect />
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<PortalAppContent portal={portal} title={title} />} />
          <Route path="/*" element={<PortalAppContent portal={portal} title={title} />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function PortalAppContent({ portal, title }: { portal: Portal; title: string }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [view, setView] = useState<View>("loading");
  const [session, setSession] = useState<SessionPayload | null>(null);
  const nav = useMemo(() => portalNav(portal), [portal]);
  const route = routeFromPathname(location.pathname);

  async function refresh() {
    try {
      const data = await getPortalMe(portal);
      setSession(data);
      setView("home");
    } catch (cause) {
      if (isApiError(cause) && cause.status === 403) {
        setView("forbidden");
        return;
      }
      if (isApiError(cause) && cause.status === 401) {
        setView("login");
        return;
      }
      setView("unauthenticated");
    }
  }

  const loginFlow = useLoginFlow({
    onSession: async () => {
      await refresh();
      navigate("/dashboard", { replace: true });
    },
  });

  useEffect(() => {
    void refresh();
  }, [portal]);

  async function onLogout() {
    try {
      await logout();
    } catch {
      // Session may already be gone.
    }
    setSession(null);
    loginFlow.resetToCredentials();
    setView("login");
    navigate("/login", { replace: true });
  }

  const active =
    nav.find((item) => {
      const itemRoute = item.href.replace(/^\/+/, "");
      return itemRoute === route || route.startsWith(`${itemRoute}/`);
    }) ?? nav[0];

  const go = (to: string) => {
    navigate(toAppPath(to));
  };

  if (view === "loading") {
    if (isAcceptInviteRoute(route)) {
      return <AcceptInviteScreen portal={portal} />;
    }
    return (
      <div className="p-5">
        <PageContentSkeleton showTable={false} />
      </div>
    );
  }

  if (isAcceptInviteRoute(route)) {
    return <AcceptInviteScreen portal={portal} />;
  }

  if (view === "login" || view === "unauthenticated") {
    if (!isLoginRoute(route)) {
      return <Navigate to="/login" replace />;
    }
    return (
      <LoginScreen
        portal={portal}
        step={loginFlow.step}
        email={loginFlow.email}
        password={loginFlow.password}
        error={
          loginFlow.error ||
          (view === "unauthenticated" && loginFlow.step === "credentials"
            ? "Authentication is required for this portal."
            : "")
        }
        submitting={loginFlow.submitting}
        challenge={loginFlow.challenge}
        onEmailChange={loginFlow.setEmail}
        onPasswordChange={loginFlow.setPassword}
        onSubmit={(event) => void loginFlow.onCredentialsSubmit(event)}
        onChallengeVerify={loginFlow.onChallengeVerify}
        onChallengeError={loginFlow.setError}
        onBackToCredentials={loginFlow.resetToCredentials}
      />
    );
  }

  if (view === "forbidden") {
    return (
      <main
        id="main"
        className="mx-auto my-12 grid max-w-md gap-3 rounded-xl border border-border-default bg-surface p-5"
      >
        <h2>403 Forbidden</h2>
        <p>This account is authenticated but is not permitted in the {portal} portal.</p>
        <button type="button" onClick={() => void onLogout()}>
          Sign out
        </button>
      </main>
    );
  }

  if (!session) {
    return null;
  }

  if (isPublicAuthRoute(route)) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <SessionProvider session={session}>
      <AppShell
        portal={portal}
        title={title}
        nav={nav}
        route={route}
        session={session}
        onLogout={() => void onLogout()}
      >
        <HighRiskRouteGate portal={portal} route={route}>
          {route === "dashboard" ? (
            portal === "platform" ? (
              <PlatformDashboard onNavigate={go} />
            ) : portal === "agency" ? (
              <AgencyDashboard onNavigate={go} />
            ) : (
              <CustomerDashboard onNavigate={go} />
            )
          ) : (
            renderProductScreen(portal, route, active.path, active.label)
          )}
        </HighRiskRouteGate>
      </AppShell>
    </SessionProvider>
  );
}
