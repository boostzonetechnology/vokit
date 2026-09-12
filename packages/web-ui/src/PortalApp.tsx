import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  ApiError,
  Portal,
  SessionPayload,
  getPortalMe,
  isApiError,
  login,
  logout,
} from "@/api";
import { AppShell } from "@/components/layout/AppShell";
import { LoginScreen } from "@/features/auth/components/LoginScreen";
import { AcceptInviteScreen } from "@/features/auth/components/AcceptInviteScreen";
import { AgencyDashboard } from "@/features/dashboard/AgencyDashboard";
import { CustomerDashboard } from "@/features/dashboard/CustomerDashboard";
import { PlatformDashboard } from "@/features/dashboard/PlatformDashboard";
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
  return (
    <BrowserRouter>
      <LegacyHashRedirect />
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<PortalAppContent portal={portal} title={title} />} />
        <Route path="/*" element={<PortalAppContent portal={portal} title={title} />} />
      </Routes>
    </BrowserRouter>
  );
}

function PortalAppContent({ portal, title }: { portal: Portal; title: string }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [view, setView] = useState<View>("loading");
  const [session, setSession] = useState<SessionPayload | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const nav = useMemo(() => portalNav(portal), [portal]);
  const route = routeFromPathname(location.pathname);

  async function refresh() {
    setError("");
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

  useEffect(() => {
    void refresh();
  }, [portal]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      await refresh();
      navigate("/dashboard", { replace: true });
    } catch (cause) {
      const apiError = cause as ApiError;
      setError(apiError.message || "Sign-in failed.");
      if (apiError.status === 401) {
        setView("login");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function onLogout() {
    try {
      await logout();
    } catch {
      // Session may already be gone.
    }
    setSession(null);
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
      <p className="p-5 text-body text-text-muted" role="status">
        Checking session…
      </p>
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
        email={email}
        password={password}
        error={
          error ||
          (view === "unauthenticated"
            ? "Authentication is required for this portal."
            : "")
        }
        submitting={submitting}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onSubmit={(event) => void onSubmit(event)}
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
    <AppShell
      portal={portal}
      title={title}
      nav={nav}
      route={route}
      session={session}
      onLogout={() => void onLogout()}
    >
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
    </AppShell>
  );
}
