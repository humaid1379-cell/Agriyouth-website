import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import { readToken, writeToken } from '../../api/client';
import { useMe } from '../../api/hooks';
import type { Me, Role } from '../../api/types';

/**
 * Demo session state.
 *
 * The browser holds only an opaque token. Role, scope, capabilities and prohibitions all
 * come from `GET /api/v1/me`, which derives them server-side; nothing here is trusted as an
 * authority claim, and the interface uses them for navigation only.
 */

interface SessionContextValue {
  token: string | null;
  me: Me | undefined;
  role: Role | undefined;
  isLoading: boolean;
  signIn: (token: string) => void;
  signOut: () => void;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => readToken());
  const { data: me, isLoading, isError } = useMe(token !== null);

  const signIn = useCallback((next: string) => {
    writeToken(next);
    setToken(next);
  }, []);

  const signOut = useCallback(() => {
    writeToken(null);
    setToken(null);
  }, []);

  const value = useMemo<SessionContextValue>(
    () => ({
      token,
      me: isError ? undefined : me,
      role: isError ? undefined : me?.role,
      isLoading: token !== null && isLoading,
      signIn,
      signOut,
    }),
    [token, me, isError, isLoading, signIn, signOut],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (context === null) throw new Error('useSession must be used inside a SessionProvider');
  return context;
}
