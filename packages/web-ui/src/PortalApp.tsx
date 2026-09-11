import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  ApiError,
  Portal,
  SessionPayload,
  getPortalMe,
  isApiError,
  login,
  logout,
} from "./api";
import { AppShell } from "./components/layout/AppShell";
import { LoginScreen } from "./features/auth/components/LoginScreen";
import { AgencyDashboard } from "./features/dashboard/AgencyDashboard";
import { CustomerDashboard } from "./features/dashboard/CustomerDashboard";
import { PlatformDashboard } from "./features/dashboard/PlatformDashboard";
import { currentRoute, portalNav } from "./nav";
import { renderProductScreen } from "./productScreens";

type View = "loading" | "login" | "home" | "unauthenticated" | "forbidden";

export function PortalApp({ portal, title }: { portal: Portal; title: string }) {
  const [view, setView] = useState<View>("loading");
  const [session, setSession] = useState<SessionPayload | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [route, setRoute] = useState(currentRoute);
  const nav = useMemo(() => portalNav(portal), [portal]);

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

  useEffect(() => {
    const onHash = () => setRoute(currentRoute());
    window.addEventListener("hashchange", onHash);
    if (!window.location.hash) {
      window.location.hash = "#/dashboard";
    }
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      await refresh();
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
  }

  const active = nav.find((item) => item.href === `#/${route}`) ?? nav[0];
  const navigate = (href: string) => {
    window.location.hash = href.startsWith("#") ? href : `#${href}`;
  };

  if (view === "loading") {
    return (
      <p className="p-5 text-body text-text-muted" role="status">
        Checking session…
      </p>
    );
  }

  if (view === "login" || view === "unauthenticated") {
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
          <PlatformDashboard onNavigate={navigate} />
        ) : portal === "agency" ? (
          <AgencyDashboard onNavigate={navigate} />
        ) : (
          <CustomerDashboard onNavigate={navigate} />
        )
      ) : (
        renderProductScreen(portal, route, active.path, active.label)
      )}
    </AppShell>
  );
}
