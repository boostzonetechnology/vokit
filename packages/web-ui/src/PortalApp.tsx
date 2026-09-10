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
import { currentRoute, portalNav } from "./nav";
import { DashboardScreen } from "./screens";
import { renderProductScreen } from "./productScreens";

type View = "loading" | "login" | "home" | "unauthenticated" | "forbidden";

export function PortalApp({ portal, title }: { portal: Portal; title: string }) {
  const [view, setView] = useState<View>("loading");
  const [session, setSession] = useState<SessionPayload | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
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
    try {
      await login(email, password);
      await refresh();
    } catch (cause) {
      const apiError = cause as ApiError;
      setError(apiError.message || "Sign-in failed.");
      if (apiError.status === 401) {
        setView("login");
      }
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

  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Skip to main content
      </a>
      <header className="topbar" role="banner">
        <div>
          <p className="eyebrow">Vokit</p>
          <h1>{title}</h1>
        </div>
        {session ? (
          <div className="session" aria-label="Signed-in session">
            <span>{session.user.email}</span>
            <span>{session.membership.role}</span>
            <button type="button" onClick={() => void onLogout()}>
              Sign out
            </button>
          </div>
        ) : null}
      </header>

      {view === "loading" && (
        <p className="pad" role="status">
          Checking session…
        </p>
      )}

      {view === "login" && (
        <main id="main" className="shell">
          <form onSubmit={onSubmit} className="card" aria-labelledby="signin-heading">
            <h2 id="signin-heading">Sign in</h2>
            <label htmlFor="email">
              Email
              <input
                id="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                autoComplete="username"
                required
              />
            </label>
            <label htmlFor="password">
              Password
              <input
                id="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                autoComplete="current-password"
                required
              />
            </label>
            {error ? (
              <p className="error" role="alert">
                {error}
              </p>
            ) : null}
            <button type="submit">Sign in</button>
          </form>
        </main>
      )}

      {view === "home" && session && (
        <div className="layout">
          <nav className="nav" aria-label="Portal">
            {nav.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className={item.href === `#/${route}` ? "active" : ""}
                aria-current={item.href === `#/${route}` ? "page" : undefined}
              >
                {item.label}
              </a>
            ))}
          </nav>
          <main id="main" className="content">
            {route === "dashboard" ? (
              <DashboardScreen
                portal={portal}
                onNavigate={(href) => {
                  window.location.hash = href;
                }}
              />
            ) : (
              renderProductScreen(portal, route, active.path, active.label)
            )}
          </main>
        </div>
      )}

      {view === "unauthenticated" && (
        <main id="main" className="shell card status">
          <h2>401 Unauthenticated</h2>
          <p>Authentication is required for this portal.</p>
          <button type="button" onClick={() => setView("login")}>
            Go to sign in
          </button>
        </main>
      )}

      {view === "forbidden" && (
        <main id="main" className="shell card status">
          <h2>403 Forbidden</h2>
          <p>This account is authenticated but is not permitted in the {portal} portal.</p>
          <button type="button" onClick={() => void onLogout()}>
            Sign out
          </button>
        </main>
      )}
    </div>
  );
}
