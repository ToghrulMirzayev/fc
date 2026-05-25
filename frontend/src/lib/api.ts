/**
 * Lightweight API client.
 *
 * - Reads access token from localStorage on every request.
 * - On 401 with token present: try /auth/refresh, retry once.
 * - On refresh failure: clear tokens and redirect to /login.
 *
 * We deliberately don't use fetch interceptors or axios — fewer moving
 * parts. Refresh logic is single-flight: parallel requests during a
 * token refresh share the same promise.
 */

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ACCESS_KEY = "auth.access";
const REFRESH_KEY = "auth.refresh";

let refreshPromise: Promise<string | null> | null = null;

export const tokens = {
  get access() {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(REFRESH_KEY);
  },
  set(access: string, refresh: string) {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

async function refreshAccessToken(): Promise<string | null> {
  // Single-flight: parallel callers share one refresh attempt.
  if (refreshPromise) return refreshPromise;
  const refresh = tokens.refresh;
  if (!refresh) return null;

  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) {
        tokens.clear();
        return null;
      }
      const data = await res.json();
      tokens.set(data.access_token, data.refresh_token);
      return data.access_token as string;
    } catch {
      tokens.clear();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export class ApiError extends Error {
  constructor(public status: number, public code: string, public detail?: string) {
    super(detail || code);
  }
}

export async function api<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const doRequest = async (token: string | null): Promise<Response> => {
    const headers = new Headers(init.headers);
    if (!headers.has("Content-Type") && init.body) {
      headers.set("Content-Type", "application/json");
    }
    if (token) headers.set("Authorization", `Bearer ${token}`);
    return fetch(`${API_URL}${path}`, { ...init, headers });
  };

  let res = await doRequest(tokens.access);

  if (res.status === 401 && tokens.refresh) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      res = await doRequest(newAccess);
    }
  }

  if (res.status === 401) {
    tokens.clear();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new ApiError(401, "unauthorized");
  }

  if (!res.ok) {
    let detail: string | undefined;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body);
    } catch {
      detail = await res.text();
    }
    throw new ApiError(res.status, detail || `http_${res.status}`, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ─── Auth ───

export async function login(email: string, password: string) {
  const data = await api<{ access_token: string; refresh_token: string }>(
    "/api/v1/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
  );
  tokens.set(data.access_token, data.refresh_token);
  return data;
}

export async function fetchMe() {
  return api<{
    id: string;
    email: string;
    full_name: string;
    role: string;
    tenant_id: string | null;
    tenant_slug: string | null;
    tenant_name: string | null;
  }>("/api/v1/auth/me");
}
