import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import { messages, type Language, type MessageKey } from './messages';

interface LanguageContextValue {
  language: Language;
  direction: 'ltr' | 'rtl';
  setLanguage: (language: Language) => void;
  toggleLanguage: () => void;
  t: (key: MessageKey) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);
const STORAGE_KEY = 'nabd.language';

function initialLanguage(): Language {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === 'ar' || stored === 'en') return stored;
    return window.navigator.language.startsWith('ar') ? 'ar' : 'en';
  } catch {
    return 'en';
  }
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(initialLanguage);
  const direction: 'ltr' | 'rtl' = language === 'ar' ? 'rtl' : 'ltr';

  // The document element carries both lang and dir so that layout mirroring, Unicode
  // directionality and screen-reader pronunciation all follow the selected language.
  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = direction;
    document.documentElement.classList.toggle('font-arabic', language === 'ar');
    try {
      window.localStorage.setItem(STORAGE_KEY, language);
    } catch {
      // Storage being unavailable only means the choice is not remembered.
    }
  }, [language, direction]);

  const setLanguage = useCallback((next: Language) => setLanguageState(next), []);
  const toggleLanguage = useCallback(
    () => setLanguageState((current) => (current === 'en' ? 'ar' : 'en')),
    [],
  );
  const t = useCallback((key: MessageKey) => messages[language][key] ?? messages.en[key], [language]);

  const value = useMemo(
    () => ({ language, direction, setLanguage, toggleLanguage, t }),
    [language, direction, setLanguage, toggleLanguage, t],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (context === null) {
    throw new Error('useLanguage must be used inside a LanguageProvider');
  }
  return context;
}

export function useTranslate(): (key: MessageKey) => string {
  return useLanguage().t;
}
