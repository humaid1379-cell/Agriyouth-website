import type { ReactNode } from 'react';

import { ApiError } from '../api/client';
import { useTranslate } from '../i18n/LanguageProvider';

/** Shared presentational primitives. Calm, restrained, and legible in grayscale. */

export function PageHeading({
  title,
  description,
  actions,
}: {
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-4">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold text-navy-deep">{title}</h1>
        {description ? (
          <p className="mt-2 max-w-prose text-sm leading-relaxed text-navy-slate">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export function Section({
  title,
  description,
  children,
  id,
}: {
  title: string;
  description?: ReactNode;
  children: ReactNode;
  id?: string;
}) {
  return (
    <section id={id} className="mb-8">
      <h2 className="mb-1 text-lg font-semibold text-navy-deep">{title}</h2>
      {description ? (
        <p className="mb-3 max-w-prose text-sm leading-relaxed text-navy-slate">{description}</p>
      ) : null}
      {children}
    </section>
  );
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-lg border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function DataList({ rows }: { rows: Array<[string, ReactNode]> }) {
  return (
    <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-[minmax(10rem,auto)_1fr]">
      {rows.map(([term, value]) => (
        <div key={term} className="contents">
          <dt className="text-sm font-medium text-navy-slate">{term}</dt>
          <dd className="break-words text-sm text-navy-deep">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Table({
  caption,
  headers,
  children,
}: {
  caption: string;
  headers: string[];
  children: ReactNode;
}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full min-w-[36rem] border-collapse text-start text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            {headers.map((header) => (
              <th
                key={header}
                scope="col"
                className="px-3 py-2 text-start text-xs font-semibold uppercase tracking-wide text-navy-slate"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Mono({ children }: { children: ReactNode }) {
  return <code className="break-all font-mono text-xs text-navy-slate">{children}</code>;
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'warn' }) {
  const classes =
    tone === 'warn'
      ? 'border-status-review/40 bg-status-review/10 text-status-review'
      : 'border-slate-300 bg-slate-50 text-navy-slate';
  return (
    <span className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${classes}`}>
      {children}
    </span>
  );
}

export function Button({
  children,
  onClick,
  type = 'button',
  variant = 'primary',
  disabled = false,
  ...rest
}: {
  children: ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit';
  variant?: 'primary' | 'secondary' | 'caution';
  disabled?: boolean;
} & Record<string, unknown>) {
  const base =
    'inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-semibold transition-colors ' +
    'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-nabd ' +
    'disabled:cursor-not-allowed disabled:opacity-50 motion-reduce:transition-none';
  const variants = {
    primary: 'bg-navy-slate text-white hover:bg-navy-deep',
    secondary: 'border border-slate-300 bg-white text-navy-deep hover:bg-slate-50',
    caution: 'border border-status-stop bg-white text-status-stop hover:bg-status-stop/10',
  } as const;
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]}`}
      {...rest}
    >
      {children}
    </button>
  );
}

export function Loading() {
  const t = useTranslate();
  return (
    <p role="status" aria-live="polite" className="py-8 text-sm text-navy-slate">
      {t('app.loading')}…
    </p>
  );
}

export function ErrorPanel({ error }: { error: unknown }) {
  const t = useTranslate();
  const apiError = error instanceof ApiError ? error : null;
  return (
    <div
      role="alert"
      className="my-4 rounded-lg border border-status-stop/40 bg-status-stop/5 p-4"
    >
      <div className="flex items-start gap-3">
        <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" className="mt-0.5 shrink-0">
          <path
            d="M8 2 H16 L22 8 V16 L16 22 H8 L2 16 V8 Z"
            fill="none"
            stroke="#A9474F"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path d="M7.5 12 H16.5" stroke="#A9474F" strokeWidth="2.4" strokeLinecap="round" />
        </svg>
        <div className="min-w-0">
          <p className="font-semibold text-status-stop">{t('error.title')}</p>
          <p className="mt-1 max-w-prose text-sm text-navy-deep">
            {apiError ? apiError.message : String(error)}
          </p>
          {apiError ? (
            <p className="mt-2 text-xs text-navy-slate">
              {t('error.code')}: <Mono>{apiError.code}</Mono>
              {' · '}
              {t('error.correlation')}: <Mono>{apiError.correlationId}</Mono>
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function NoticeList({
  notices,
  language,
  heading,
}: {
  notices: Array<{ notice_id: string; heading_en: string; text_en: string; heading_ar: string; text_ar: string }>;
  language: 'en' | 'ar';
  heading?: string;
}) {
  return (
    <section aria-label={heading ?? 'Notices'} className="my-6 space-y-3">
      {heading ? <h2 className="text-lg font-semibold text-navy-deep">{heading}</h2> : null}
      {notices.map((notice) => (
        <div
          key={notice.notice_id}
          className="rounded-lg border-s-4 border-s-violet-authority border-y border-e border-slate-200 bg-white p-4"
        >
          <p className="text-sm font-semibold text-navy-deep">
            {language === 'ar' ? notice.heading_ar : notice.heading_en}
          </p>
          <p className="mt-1 max-w-prose text-sm leading-relaxed text-navy-slate">
            {language === 'ar' ? notice.text_ar : notice.text_en}
          </p>
        </div>
      ))}
    </section>
  );
}

export function StatusDimensions({
  status,
  labels,
}: {
  status: { built: string; integration: string; operational: string; authorization: string };
  labels: { built: string; integration: string; operational: string; authorization: string };
}) {
  const entries: Array<[string, string]> = [
    [labels.built, status.built],
    [labels.integration, status.integration],
    [labels.operational, status.operational],
    [labels.authorization, status.authorization],
  ];
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {entries.map(([label, value]) => (
        <div key={label} className="rounded-lg border border-slate-200 bg-white p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-navy-slate">{label}</p>
          <p className="mt-1 font-mono text-sm font-semibold text-navy-deep">{value}</p>
        </div>
      ))}
    </div>
  );
}
