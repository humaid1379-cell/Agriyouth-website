import { useNavigate } from 'react-router-dom';

import { useCreateSession, useDemoIdentities } from '../api/hooks';
import { Button, Card, ErrorPanel, Loading, PageHeading } from '../components/ui';
import { useSession } from '../features/session/SessionContext';
import { useLanguage } from '../i18n/LanguageProvider';

/**
 * Demo profile selection.
 *
 * There is no password field and no shared-password pattern, because there is no real
 * identity system behind this screen. Selecting a profile asks the server to issue a
 * short-lived signed demo session; the browser never asserts a role.
 */
export function LoginPage() {
  const { language, t } = useLanguage();
  const { signIn, token, me } = useSession();
  const navigate = useNavigate();
  const identities = useDemoIdentities();
  const createSession = useCreateSession();

  if (token !== null && me !== undefined) {
    navigate(me.role === 'ADMINISTRATOR' ? '/settings' : '/cases', { replace: true });
  }

  return (
    <>
      <PageHeading title={t('login.title')} description={t('login.intro')} />

      {identities.isLoading ? <Loading /> : null}
      {identities.error ? <ErrorPanel error={identities.error} /> : null}
      {createSession.error ? <ErrorPanel error={createSession.error} /> : null}

      <ul className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {(identities.data ?? []).map((identity) => (
          <li key={identity.identity_id}>
            <Card className="flex h-full flex-col">
              <h2 className="text-base font-semibold text-navy-deep">
                {language === 'ar' ? identity.display_name_ar : identity.display_name_en}
              </h2>
              <p className="mt-1 font-mono text-xs text-navy-slate">{identity.identity_id}</p>

              <div className="mt-4 space-y-3 text-sm">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-navy-slate">
                    {t('login.capabilities')}
                  </p>
                  <ul className="mt-1 list-disc space-y-0.5 ps-5 text-navy-deep">
                    {identity.capabilities.map((capability) => (
                      <li key={capability} className="font-mono text-xs">
                        {capability}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-navy-slate">
                    {t('login.prohibitions')}
                  </p>
                  <ul className="mt-1 list-disc space-y-0.5 ps-5 text-navy-deep">
                    {identity.prohibitions.map((prohibition) => (
                      <li key={prohibition} className="font-mono text-xs">
                        {prohibition}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-auto pt-4">
                <Button
                  onClick={() => {
                    createSession.mutate(identity.identity_id, {
                      onSuccess: (session) => {
                        signIn(session.token);
                        navigate(session.role === 'ADMINISTRATOR' ? '/settings' : '/cases');
                      },
                    });
                  }}
                  disabled={createSession.isPending}
                >
                  {t('login.continue')}
                </Button>
              </div>
            </Card>
          </li>
        ))}
      </ul>
    </>
  );
}
