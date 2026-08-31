import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useExcerpt, useSourcePage } from '../api/hooks';
import { Badge, Card, DataList, ErrorPanel, Loading, Mono, PageHeading, Section } from '../components/ui';
import { useTranslate } from '../i18n/LanguageProvider';

/**
 * Exact evidence view. Read-only by construction: there is no edit control anywhere on this
 * screen, and the API exposes no mutation for source content.
 */
export function EvidencePage() {
  const t = useTranslate();
  const { caseId = '', excerptId = '' } = useParams();
  const excerpt = useExcerpt(excerptId);
  const [showPage, setShowPage] = useState(false);
  const sourcePage = useSourcePage(
    excerpt.data?.source_id ?? '',
    excerpt.data?.page_number ?? 1,
    showPage && excerpt.data !== undefined,
  );

  if (excerpt.isLoading) return <Loading />;
  if (excerpt.error) return <ErrorPanel error={excerpt.error} />;
  if (!excerpt.data) return null;

  const item = excerpt.data;

  return (
    <>
      <PageHeading
        title={t('evidence.title')}
        description={item.citation_label}
        actions={
          <Link className="text-sm underline hover:no-underline" to={`/cases/${caseId}/packet`}>
            {t('evidence.backToPacket')}
          </Link>
        }
      />

      {item.revocation_warning ? (
        <div role="note" className="mb-4 rounded-lg border border-status-review/40 bg-status-review/5 p-4">
          <p className="text-sm font-semibold text-status-review">{t('evidence.revoked')}</p>
          <p className="mt-1 max-w-prose text-sm text-navy-deep">{item.revocation_warning}</p>
        </div>
      ) : null}

      <Card className="mb-6">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Badge tone="warn">{t('evidence.untrusted')}</Badge>
          <span className="font-mono text-xs text-navy-slate">{item.trust_label}</span>
        </div>
        <p className="mb-4 max-w-prose text-xs leading-relaxed text-navy-slate">
          {t('evidence.untrustedExplain')}
        </p>
        <blockquote className="border-s-4 border-slate-300 bg-slate-50 p-4 text-sm leading-relaxed text-navy-deep">
          {item.text}
        </blockquote>
        <p className="mt-3 text-xs text-navy-slate">{t('evidence.readOnly')}</p>
      </Card>

      <Section title={t('evidence.source')}>
        <Card>
          <DataList
            rows={[
              [t('evidence.source'), `${item.source_title} (${item.source_id}@${item.source_version})`],
              ['Authority class', <Mono key="a">{item.authority_class}</Mono>],
              ['Lifecycle', <Mono key="l">{item.lifecycle}</Mono>],
              [t('evidence.page'), String(item.page_number)],
              [t('evidence.section'), item.section_heading],
              [t('evidence.offsets'), <Mono key="o">{`${item.char_start}–${item.char_end}`}</Mono>],
              [t('evidence.hash'), <Mono key="h">{item.text_sha256}</Mono>],
            ]}
          />
        </Card>
      </Section>

      <Section title={t('evidence.openSourcePage')}>
        <button
          type="button"
          onClick={() => setShowPage((current) => !current)}
          aria-expanded={showPage}
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-nabd"
        >
          {t('evidence.openSourcePage')}
        </button>
        {showPage && sourcePage.error ? <ErrorPanel error={sourcePage.error} /> : null}
        {showPage && sourcePage.data ? (
          <Card className="mt-4">
            <p className="mb-2 text-sm font-semibold text-navy-deep">
              {sourcePage.data.title} — {t('evidence.page')} {sourcePage.data.page_number} /{' '}
              {sourcePage.data.page_count}
            </p>
            <p className="mb-3 font-mono text-xs text-navy-slate">
              {sourcePage.data.section_headings.join(' · ')}
            </p>
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words bg-slate-50 p-4 text-xs leading-relaxed text-navy-deep">
              {sourcePage.data.text}
            </pre>
          </Card>
        ) : null}
      </Section>
    </>
  );
}
