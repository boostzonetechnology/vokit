export type Portal = "platform" | "agency" | "customer";

export type ApiError = {
  code: string;
  message: string;
  status: number;
};

export type SessionPayload = {
  user: { id: string; email: string; status: string };
  membership: {
    id: string;
    principal_type: string;
    role: string;
    tenant_id: string | null;
    customer_id: string | null;
    status: string;
  };
  permissions: string[];
};

export type DashboardCard = {
  key: string;
  label: string;
  value: string | number | boolean;
  href: string;
};

export type DashboardPayload = {
  period: { preset: string; timezone: string; start: string; end: string };
  source: string;
  currency?: string;
  kpis: DashboardCard[];
  financial?: Record<string, string | number>;
  alerts?: Record<string, string | number | boolean>;
  recent_calls?: Array<Record<string, string | number>>;
  failed_calls?: number;
};

async function parse<T>(response: Response): Promise<T> {
  const body = await response.json();
  if (!response.ok) {
    const error: ApiError = {
      code: body?.error?.code ?? "request_error",
      message: body?.error?.message ?? "The request could not be processed.",
      status: response.status,
    };
    throw error;
  }
  return body.data as T;
}

export async function getCsrf(): Promise<string> {
  const response = await fetch("/api/v1/auth/csrf", { credentials: "include" });
  const data = await parse<{ csrf_token: string }>(response);
  return data.csrf_token;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(path, { credentials: "include" });
  return parse<T>(response);
}

export async function apiSend<T>(
  path: string,
  method: "POST" | "PUT" | "PATCH",
  payload: Record<string, unknown> = {},
  headers: Record<string, string> = {},
): Promise<T> {
  const csrf = await getCsrf();
  const response = await fetch(path, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf,
      ...headers,
    },
    body: JSON.stringify(payload),
  });
  return parse<T>(response);
}

export async function login(email: string, password: string): Promise<SessionPayload> {
  return apiSend<SessionPayload>("/api/v1/auth/login", "POST", { email, password });
}

export async function logout(): Promise<void> {
  await apiSend("/api/v1/auth/logout", "POST", {});
}

export async function getPortalMe(portal: Portal): Promise<SessionPayload> {
  return apiGet<SessionPayload>(`/api/v1/${portal}/me`);
}

export async function getDashboard(
  portal: Portal,
  options: {
    period: string;
    timezone: string;
    since?: string;
    until?: string;
    agencyId?: string;
  },
): Promise<DashboardPayload> {
  const params = new URLSearchParams({
    period: options.period,
    timezone: options.timezone,
  });
  if (options.since) {
    params.set("since", options.since);
  }
  if (options.until) {
    params.set("until", options.until);
  }
  if (options.agencyId) {
    params.set("agency_id", options.agencyId);
  }
  return apiGet<DashboardPayload>(`/api/v1/${portal}/dashboard?${params.toString()}`);
}

export function isApiError(value: unknown): value is ApiError {
  return Boolean(value && typeof value === "object" && "status" in value && "code" in value);
}
