const TOKEN_KEY = 'hifzai:token';
const REFRESH_TOKEN_KEY = 'hifzai:refreshToken';
const STAY_SIGNED_IN_KEY = 'hifzai:staySignedIn';

export const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

export function resolveMediaUrl(path: string): string {
  return new URL(path, API_BASE_URL).toString();
}

/**
 * "Stay signed in" (LoginPage) decides where session tokens live:
 * localStorage survives closing the browser entirely; sessionStorage is
 * wiped the moment the tab/browser closes. The choice itself always lives
 * in localStorage (it's just a flag, not sensitive) so a page reload knows
 * which storage to read the real tokens back from. Missing entirely —
 * e.g. a session that started before this feature existed — defaults to
 * localStorage, preserving the app's original always-persistent behavior
 * so nobody already logged in gets silently signed out by this change.
 */
function activeStorage(): Storage {
  return localStorage.getItem(STAY_SIGNED_IN_KEY) === 'false' ? sessionStorage : localStorage;
}

/** Call once at login/register, before storing tokens, to pick (and remember) this session's storage. */
export function beginSession(staySignedIn: boolean): void {
  const inactive = staySignedIn ? sessionStorage : localStorage;
  inactive.removeItem(TOKEN_KEY);
  inactive.removeItem(REFRESH_TOKEN_KEY);
  localStorage.setItem(STAY_SIGNED_IN_KEY, String(staySignedIn));
}

/** Clears tokens from both storages unconditionally — used on logout/forced logout. */
export function endSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(STAY_SIGNED_IN_KEY);
}

export function getToken(): string | null {
  return activeStorage().getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) activeStorage().setItem(TOKEN_KEY, token);
  else activeStorage().removeItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return activeStorage().getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token: string | null): void {
  if (token) activeStorage().setItem(REFRESH_TOKEN_KEY, token);
  else activeStorage().removeItem(REFRESH_TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  /** Pass a FormData body as-is (for multipart uploads) instead of JSON-encoding it. */
  formData?: FormData;
  query?: Record<string, string | number | undefined>;
  /** Internal: set on the retry attempt so a second 401 doesn't loop forever. */
  _isRetry?: boolean;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const url = new URL(path, API_BASE_URL);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

/**
 * Phase 17: access tokens are short-lived (15 min) now that refresh
 * tokens exist. On a 401 from anything other than the auth endpoints
 * themselves, this attempts exactly one silent refresh and retries the
 * original request — the rest of the app never has to think about token
 * expiry. If the refresh itself fails (refresh token also expired or
 * revoked), the session is really over: tokens are cleared and the app
 * hard-redirects to /login, since apiClient has no router access to do
 * this more gracefully from outside a React component.
 *
 * Bugfix: the backend rotates refresh tokens (each one is revoked as
 * soon as it's used — see `auth.py`'s `/auth/refresh`), so if several
 * requests hit a 401 around the same time (e.g. a dashboard firing off
 * multiple fetches at once right after the access token expires), each
 * one independently racing to redeem the *same* refresh token meant only
 * the first would succeed — every other caller would see its refresh
 * rejected and force a real logout, discarding the fresh tokens the
 * winner had just stored. `inFlightRefresh` makes every concurrent
 * caller await the one shared refresh attempt instead of each starting
 * its own, so a burst of parallel requests can no longer log the user
 * out by racing each other.
 */
let inFlightRefresh: Promise<boolean> | null = null;

async function attemptRefresh(): Promise<boolean> {
  if (inFlightRefresh) return inFlightRefresh;

  inFlightRefresh = (async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await fetch(buildUrl('/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken }),
      });
      if (!response.ok) return false;

      const data = await response.json();
      setToken(data.accessToken);
      setRefreshToken(data.refreshToken);
      return true;
    } catch {
      return false;
    }
  })();

  try {
    return await inFlightRefresh;
  } finally {
    inFlightRefresh = null;
  }
}

function forceLogout(): void {
  endSession();
  localStorage.removeItem('hifzai:user');
  sessionStorage.removeItem('hifzai:user');
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

/**
 * Every service module in `src/services` that talks to the backend goes
 * through this one function — token attachment, base URL, refresh-on-401,
 * and error shape are handled in exactly one place.
 */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  let body: BodyInit | undefined;
  if (options.formData) {
    body = options.formData; // browser sets multipart Content-Type + boundary itself
  } else if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(options.body);
  }

  const response = await fetch(buildUrl(path, options.query), {
    method: options.method ?? 'GET',
    headers,
    body,
  });

  if (response.status === 401 && !options._isRetry && !path.startsWith('/auth/')) {
    const refreshed = await attemptRefresh();
    if (refreshed) {
      return apiFetch<T>(path, { ...options, _isRetry: true });
    }
    forceLogout();
  }

  if (!response.ok) {
    let message = response.statusText;
    try {
      const errorBody = await response.json();
      message = errorBody.detail ?? message;
    } catch {
      // response wasn't JSON — fall back to statusText
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
