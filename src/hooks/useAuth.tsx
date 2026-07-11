import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import * as authService from '@/services/authService';
import { getToken } from '@/services/apiClient';
import type { AuthUser } from '@/types/auth';
import type { LoginInput, RegisterInput } from '@/services/authService';

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (input: LoginInput) => Promise<AuthUser>;
  register: (input: RegisterInput) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    // A stored user with no token (e.g. cleared manually) shouldn't count as logged in.
    return getToken() ? authService.getStoredUser() : null;
  });

  const login = useCallback(async (input: LoginInput) => {
    const loggedInUser = await authService.login(input);
    setUser(loggedInUser);
    return loggedInUser;
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    const registeredUser = await authService.register(input);
    setUser(registeredUser);
    return registeredUser;
  }, []);

  const logout = useCallback(() => {
    setUser(null); // clear local state immediately; no need to wait on the network call
    void authService.logout();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: user !== null, login, register, logout }),
    [user, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
