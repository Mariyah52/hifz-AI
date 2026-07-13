import { apiFetch, beginSession, endSession, getRefreshToken, setRefreshToken, setToken } from './apiClient';
import type { AuthUser } from '@/types/auth';
import type { UserRole } from '@/types/user';

const USER_KEY = 'hifzai:user';

interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  role: UserRole;
  userId: string;
  name: string;
  organizationSlug: string;
}

export interface LoginInput {
  email: string;
  password: string;
  /** Defaults to true — matches the app's original always-persistent-session behavior. */
  staySignedIn?: boolean;
}

export interface RegisterInput {
  email: string;
  password: string;
  name: string;
  role: UserRole;
  classId?: string;
  childStudentId?: string;
  /** Required unless role === 'admin' — the code for the existing institution being joined. */
  organizationSlug?: string;
  /** Required when role === 'admin' — creates a brand-new institution instead of joining one. */
  organizationName?: string;
}

function toAuthUser(res: TokenResponse): AuthUser {
  return { id: res.userId, name: res.name, role: res.role, organizationSlug: res.organizationSlug };
}

function persistTokens(res: TokenResponse, staySignedIn: boolean): void {
  // Must run before setToken/setRefreshToken — it decides which storage
  // (localStorage vs sessionStorage) those two actually write into.
  beginSession(staySignedIn);
  setToken(res.accessToken);
  setRefreshToken(res.refreshToken);
  (staySignedIn ? localStorage : sessionStorage).setItem(USER_KEY, JSON.stringify(toAuthUser(res)));
}

/** Reads back whoever was last logged in, so a page reload doesn't lose the session. */
export function getStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY) ?? sessionStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export async function login(input: LoginInput): Promise<AuthUser> {
  const staySignedIn = input.staySignedIn ?? true;
  const res = await apiFetch<TokenResponse>('/auth/login', {
    method: 'POST',
    body: { email: input.email, password: input.password, staySignedIn },
  });
  persistTokens(res, staySignedIn);
  return toAuthUser(res);
}

export async function register(input: RegisterInput): Promise<AuthUser> {
  const res = await apiFetch<TokenResponse>('/auth/register', { method: 'POST', body: input });
  // Registering is already an explicit, deliberate action (no checkbox
  // offered here) — stays signed in by default, same as before this feature.
  persistTokens(res, true);
  return toAuthUser(res);
}

export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken();
  if (refreshToken) {
    // Best-effort: revoke the refresh token server-side so it can't be
    // replayed later. Still clear local state even if this call fails
    // (e.g. already offline) — the user's own session should always be
    // able to end locally regardless of network state.
    try {
      await apiFetch<void>('/auth/logout', { method: 'POST', body: { refreshToken } });
    } catch {
      // ignored — see comment above
    }
  }
  endSession();
  localStorage.removeItem(USER_KEY);
  sessionStorage.removeItem(USER_KEY);
}

export function requestPasswordReset(email: string): Promise<void> {
  return apiFetch<void>('/auth/request-password-reset', { method: 'POST', body: { email } });
}

export function resetPassword(token: string, newPassword: string): Promise<void> {
  return apiFetch<void>('/auth/reset-password', { method: 'POST', body: { token, newPassword } });
}
