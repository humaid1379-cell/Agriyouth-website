import { NavLink, Outlet, useNavigate } from 'react-router-dom';

import { useSession } from '../features/session/SessionContext';
import { useLanguage } from '../i18n/LanguageProvider';

import type { Role } from '../api/types';
import type { MessageKey } from '../i18n/messages';

interface NavItem {
  to: string;
  key: MessageKey;
  roles: readonly Role[];
}

const NAV: readonly NavItem[] = [
  { to: '/cases', key: 'nav.cases', roles: ['REQUESTER', 'REVIEWER'] },
  { to: '/cases/new', key: 'nav.newCase', roles: ['REQUESTER'] },
  { to: '/review', key: 'nav.review', roles: ['REVIEWER'] },
  { to: '/assurance', key: 'nav.assurance', roles: ['REQUESTER', 'REVIEWER', 'ADMINISTRATOR'] },
  { to: '/settings', key: 'nav.settings', roles: ['ADMINISTRATOR'] },
];

export function Layout() {
  const { language, direction, toggleLanguage, t } = useLanguage();
  const { me, signOut } = useSession();
  const navigate = useNavigate();

  const visible = NAV.filter((item) => (me ? item.roles.includes(me.role) : false));

  return (
    <div className="min-h-screen bg-soft text-navy-deep" dir={direction}>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:start-4 focus:top-4 focus:z-50 focus:rounded focus:bg-white focus:px-4 focus:py-2 focus:text-navy-deep focus:outline focus:outline-2 focus:outline-cyan-nabd"
      >
        {t('app.skipToContent')}
      </a>

      <header className="border-b border-navy-slate/20 bg-navy-deep text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="min-w-0">
            <p className={`text-lg font-semibold ${language === 'ar' ? 'font-kufi' : ''}`}>
              {t('app.name')}
            </p>
            <p className="text-xs text-cyan-nabd">{t('app.tagline')}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs">
            <span className="rounded border border-white/25 px-2 py-1">
              {t('app.environment')}: <span className="font-mono">ISOLATED_PROTOTYPE_V1</span>
            </span>
            <span className="rounded border border-white/25 px-2 py-1">{t('app.syntheticOnly')}</span>
            <button
              type="button"
              onClick={toggleLanguage}
              lang={language === 'en' ? 'ar' : 'en'}
              className="rounded border border-white/40 px-3 py-1 font-semibold hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-nabd"
            >
              {language === 'en' ? t('app.switchToArabic') : t('app.switchToEnglish')}
            </button>
            {me ? (
              <button
                type="button"
                onClick={() => {
                  signOut();
                  navigate('/login');
                }}
                className="rounded border border-white/40 px-3 py-1 hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-nabd"
              >
                {t('app.signOut')}
              </button>
            ) : null}
          </div>
        </div>

        {me ? (
          <div className="border-t border-white/10 bg-navy-slate">
            <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-1 px-2 py-1">
              <nav aria-label="Primary" className="flex flex-wrap gap-1">
                {visible.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/cases'}
                    className={({ isActive }) =>
                      `rounded px-3 py-2 text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-nabd ${
                        isActive ? 'bg-white text-navy-deep' : 'text-white hover:bg-white/10'
                      }`
                    }
                  >
                    {t(item.key)}
                  </NavLink>
                ))}
              </nav>
              <span className="ms-auto px-3 py-2 text-xs text-white/80">
                {language === 'ar' ? me.display_name_ar : me.display_name_en}
                <span className="ms-2 font-mono">{me.role}</span>
              </span>
            </div>
          </div>
        ) : null}
      </header>

      <main id="main" className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 text-xs leading-relaxed text-navy-slate">
          <p className="max-w-prose">
            {language === 'ar'
              ? 'نموذج أولي معزول يستخدم بيانات اصطناعية فقط. لدعم القرار فقط: لا يوافق على أي إجراء مؤسسي ولا ينفّذه ولا يرسله ولا يفعّله.'
              : 'Isolated prototype using synthetic data only. Decision-support only: it does not approve, execute, transmit or activate any institutional action.'}
          </p>
          <p className="mt-2 font-mono">
            Built: NOT_EVIDENCED · Integration: NOT_EVIDENCED · Operational: NOT_EVIDENCED ·
            Authorization: NOT_GRANTED
          </p>
        </div>
      </footer>
    </div>
  );
}
