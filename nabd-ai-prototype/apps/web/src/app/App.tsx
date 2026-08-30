import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';

import { SessionProvider, useSession } from '../features/session/SessionContext';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { Loading } from '../components/ui';
import { AssurancePage } from '../routes/AssurancePage';
import { AuditPage } from '../routes/AuditPage';
import { CasesPage } from '../routes/CasesPage';
import { EvidencePage } from '../routes/EvidencePage';
import { LineagePage } from '../routes/LineagePage';
import { LoginPage } from '../routes/LoginPage';
import { NewCasePage } from '../routes/NewCasePage';
import { PacketPage } from '../routes/PacketPage';
import { ProgressPage } from '../routes/ProgressPage';
import { ReviewCasePage } from '../routes/ReviewCasePage';
import { ReviewQueuePage } from '../routes/ReviewQueuePage';
import { SettingsPage } from '../routes/SettingsPage';
import { Layout } from './Layout';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 5_000 },
    mutations: { retry: 0 },
  },
});

function RequireSession({ children }: { children: React.ReactNode }) {
  const { token, me, isLoading } = useSession();
  if (token === null) return <Navigate to="/login" replace />;
  if (isLoading) return <Loading />;
  if (me === undefined) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <Router>
          <SessionProvider>
            <Routes>
              <Route element={<Layout />}>
                <Route path="/login" element={<LoginPage />} />
                <Route
                  path="/cases"
                  element={
                    <RequireSession>
                      <CasesPage />
                    </RequireSession>
                  }
                />
                <Route
                  path="/cases/new"
                  element={
                    <RequireSession>
                      <NewCasePage />
                    </RequireSession>
                  }
                />
                <Route
                  path="/cases/:caseId/progress"
                  element={
                    <RequireSession>
                      <ProgressPage />
                    </RequireSession>
                  }
                />
                <Route
                  path="/cases/:caseId/packet"
                  element={
                    <RequireSession>
                      <PacketPage />
                    </RequireSession>
                  }
                />
                <Route
                  path="/cases/:caseId/evidence/:excerptId"
                  element={
                    <RequireSession>
                      <EvidencePage />
                    </RequireSession>
                  }
                />
                <Route
                  path="/cases/:caseId/audit"
                  element={
                    <RequireSession>
                      <AuditPage />
                    </RequireSession>
                  }
                />
                <Route
                  path="/cases/:caseId/lineage"
                  element={
                    <RequireSession>
                      <LineagePage />
                    </RequireSession>
                  }
                />
                <Route
                  path="/review"
                  element={
                    <RequireSession>
                      <ReviewQueuePage />
                    </RequireSession>
                  }
                />
                <Route
                  path="/review/:caseId"
                  element={
                    <RequireSession>
                      <ReviewCasePage />
                    </RequireSession>
                  }
                />
                <Route
                  path="/assurance"
                  element={
                    <RequireSession>
                      <AssurancePage />
                    </RequireSession>
                  }
                />
                <Route
                  path="/settings"
                  element={
                    <RequireSession>
                      <SettingsPage />
                    </RequireSession>
                  }
                />
                <Route path="*" element={<Navigate to="/cases" replace />} />
              </Route>
            </Routes>
          </SessionProvider>
        </Router>
      </LanguageProvider>
    </QueryClientProvider>
  );
}
