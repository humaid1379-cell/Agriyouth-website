import { useParams } from 'react-router-dom';

import { useAudit } from '../api/hooks';
import { Card, ErrorPanel, Loading, Mono, PageHeading, Table } from '../components/ui';
import { useTranslate } from '../i18n/LanguageProvider';

export function AuditPage() {
  const t = useTranslate();
  const { caseId = '' } = useParams();
  const audit = useAudit(caseId);

  if (audit.isLoading) return <Loading />;
  if (audit.error) return <ErrorPanel error={audit.error} />;
  if (!audit.data) return null;

  const { events, verification } = audit.data;

  return (
    <>
      <PageHeading title={t('audit.title')} description={t('audit.tamperNote')} />

      <Card className="mb-6">
        <div className="flex items-start gap-3">
          <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true" className="shrink-0">
            {verification.verified ? (
              <>
                <rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="#133047" strokeWidth="2" />
                <path d="M7.5 12.5 L10.5 15.5 L16.5 8.5" fill="none" stroke="#133047" strokeWidth="2" strokeLinecap="round" />
              </>
            ) : (
              <>
                <path d="M8 2 H16 L22 8 V16 L16 22 H8 L2 16 V8 Z" fill="none" stroke="#A9474F" strokeWidth="2" strokeLinejoin="round" />
                <path d="M7.5 12 H16.5" stroke="#A9474F" strokeWidth="2.4" strokeLinecap="round" />
              </>
            )}
          </svg>
          <div>
            <p className={verification.verified ? 'font-semibold text-navy-deep' : 'font-semibold text-status-stop'}>
              {verification.verified ? t('audit.chainVerified') : t('audit.chainDiverged')}
            </p>
            <p className="mt-1 text-sm text-navy-slate">
              {verification.event_count} {t('audit.events')} · <Mono>{verification.chain_version}</Mono>
            </p>
            {!verification.verified ? (
              <p className="mt-1 text-sm text-status-stop">
                {verification.first_divergence_kind} at sequence {verification.first_divergence_sequence}
              </p>
            ) : null}
          </div>
        </div>
      </Card>

      <Table
        caption={t('audit.title')}
        headers={[
          t('audit.sequence'),
          t('audit.type'),
          t('audit.outcome'),
          t('audit.actor'),
          t('audit.hash'),
        ]}
      >
        {events.map((event) => (
          <tr key={event.event_id} className="border-b border-slate-100 last:border-b-0">
            <td className="px-3 py-2 font-mono text-xs">{event.sequence}</td>
            <td className="px-3 py-2">
              <span className="font-mono text-xs font-semibold text-navy-deep">{event.event_type}</span>
              {event.from_state ? (
                <p className="font-mono text-[0.65rem] text-navy-slate">
                  {event.from_state} {'\u2192'} {event.to_state}
                </p>
              ) : null}
              {event.reason_code ? (
                <p className="font-mono text-[0.65rem] text-status-stop">{event.reason_code}</p>
              ) : null}
            </td>
            <td className="px-3 py-2 text-xs">
              {event.outcome}
              {event.confirmed ? <span className="ms-1 text-navy-slate">{'\u2713'}</span> : null}
              {event.severity ? (
                <p className="font-mono text-[0.65rem] text-status-stop">{event.severity}</p>
              ) : null}
            </td>
            <td className="px-3 py-2 font-mono text-[0.65rem]">{event.actor_id}</td>
            <td className="px-3 py-2">
              <p className="font-mono text-[0.6rem] text-navy-slate">
                {event.previous_event_hash.slice(0, 12)}… {'\u2192'} {event.event_hash.slice(0, 12)}…
              </p>
            </td>
          </tr>
        ))}
      </Table>
    </>
  );
}
