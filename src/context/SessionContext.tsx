import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import type { LoginRequest, PermissionCode, RoleCode, Session } from '../types/domain';

interface SessionContextValue {
  session: Session | null;
  isAuthenticated: boolean;
  isRestoring: boolean;
  login: (request: LoginRequest) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: PermissionCode) => boolean;
  switchDemoRole: (role: RoleCode) => Promise<void>;
}

const STORAGE_KEY = 'smart-city-session';
const roleCodes: RoleCode[] = ['modeler', 'analyst', 'admin'];

const SessionContext = createContext<SessionContextValue | null>(null);

const isValidSession = (value: unknown): value is Session => {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<Session>;
  if (typeof candidate.token !== 'string' || typeof candidate.expiresAt !== 'string') return false;
  if (!candidate.user || typeof candidate.user !== 'object') return false;
  const user = candidate.user as Partial<Session['user']>;
  return (
    typeof user.id === 'string' &&
    typeof user.name === 'string' &&
    typeof user.email === 'string' &&
    typeof user.department === 'string' &&
    roleCodes.includes(user.role as RoleCode) &&
    Array.isArray(user.permissions) &&
    user.permissions.every((permission) => typeof permission === 'string')
  );
};

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as unknown;
        if (isValidSession(parsed) && new Date(parsed.expiresAt).getTime() > Date.now()) {
          setSession(parsed);
        } else {
          localStorage.removeItem(STORAGE_KEY);
        }
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setIsRestoring(false);
  }, []);

  const persist = useCallback((nextSession: Session | null) => {
    setSession(nextSession);
    if (nextSession) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const login = useCallback(
    async (request: LoginRequest) => {
      const response = await api.login(request);
      persist(response.data);
    },
    [persist],
  );

  const logout = useCallback(() => {
    persist(null);
  }, [persist]);

  const hasPermission = useCallback(
    (permission: PermissionCode) => Boolean(session?.user.permissions.includes(permission)),
    [session],
  );

  const switchDemoRole = useCallback(
    async (role: RoleCode) => {
      const response = await api.login({ email: `${role}@nku.city`, password: 'demo1234', role });
      persist(response.data);
    },
    [persist],
  );

  const value = useMemo<SessionContextValue>(
    () => ({
      session,
      isAuthenticated: Boolean(session),
      isRestoring,
      login,
      logout,
      hasPermission,
      switchDemoRole,
    }),
    [hasPermission, isRestoring, login, logout, session, switchDemoRole],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used inside SessionProvider');
  }
  return context;
}
