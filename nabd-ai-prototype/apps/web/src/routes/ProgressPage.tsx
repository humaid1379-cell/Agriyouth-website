import { Link, useParams } from 'react-router-dom';

import { useProgress } from '../api/hooks';
import { StatusIndicator, statusKindFor } from '../components/StatusIndicator';
import { Card, ErrorPanel, Loading, Mono, PageHeading, Section, Table } from '../components/ui';
import { useTranslate } from '../i18n/LanguageProvider';

export function ProgressPage() {
  const t = useTranslate();
  const { caseId = '' } = useParams();
  const progress = useProgress(caseId);

  if (progress.isLoading) return <Loading />;
  if (progress.error) return <ErrorPanel error={progress.error} />;
  if (!progress.data) return null;

  const { case: summary, transitions, rule_results: rules, limits, stop_record: stop } = progress.data;
  const failures = rules.filter((rule) => rule.outcome === 'FAIL');

  return (
    <>
      <PageHeading
        title={t('progress.title')}
        description={summary.normalised_question}
        actions={
          summary.packet_available ? (
            <Link
              className="text-sm underline hover:no-underline"
              to={`/cases/${caseId}/packet`}
            >
              {t('cases.viewPacket')}
            </Link>
          ) : null
        }
      />

      <Card className="mb-6">
        <StatusIndicator
          kind={statusKindFor(summary.current_state, summary.route)}
          withDetail
          suffix={summary.current_state}
        />
        {summary.reason_message ? (
          <p className="mt-3 max-w-prose text-sm text-navy-deep">
            <span className="font-mono text-xs">{summary.reason_code}</span> — {summary.reason_message}
          </p>
        ) : null}
      </Card>

      {stop ? (
        <Section title={t('progress.stopRecord')}>
          <Card>
            <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs text-navy-slate">
              {JSON.stringify(
                { failed_state: stop.failed_state, reason_code: stop.reason_code, message: stop.message },
                null,
                2,
              )}
            </pre>
          </Card>
        </Section>
      ) : null}

      <Section title={t('progress.timeline')}>
        <ol className="relative space-y-3">
          {transitions.map((transition) => (
            <li
              key={transition.sequence}
              className="rounded-lg border border-slate-200 bg-white p-3"
            >
              <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <span className="font-mono text-xs text-navy-slate">
                  {String(transition.sequence).padStart(2, '0')}
                </span>
                <span className="font-mono text-sm font-semibold text-navy-deep">
                  {transition.to_state}
                </span>
                {transition.from_state ? (
                  <span className="text-xs text-navy-slate">
                    {t('progress.from')} <Mono>{transition.from_state}</Mono>
                  </span>
                ) : null}
                <span className="ms-auto text-xs text-navy-slate">
                  {new Date(transition.occurred_at).toISOString().replace('T', ' ').slice(0, 19)}Z
                </span>
              </div>
              {transition.reason_code ? (
                <p className="mt-1 text-sm text-status-stop">
                  <Mono>{transition.reason_code}</Mono>
                  {transition.reason_message ? ` — ${transition.reason_message}` : null}
                </p>
              ) : null}
            </li>
          ))}
        </ol>
      </Section>

      <Section
        title={t('progress.ruleResults')}
        description={`${rules.length} evaluations, ${failures.length} failing.`}
      >
        <Table
          caption={t('progress.ruleResults')}
          headers={[
            t('progress.rule'),
            t('progress.outcome'),
            t('progress.reason'),
            t('progress.effect'),
            t('progress.precedence'),
          ]}
        >
          {rules.map((rule, index) => (
            <tr
              key={`${rule.rule_id}-${index}`}
              className="border-b border-slate-100 last:border-b-0"
            >
              <td className="px-3 py-2 font-mono text-xs">{rule.rule_id}</td>
              <td className="px-3 py-2">
                <span
                  className={
                    rule.outcome === 'FAIL'
                      ? 'font-semibold text-status-stop'
                      : 'text-navy-slate'
                  }
                >
                  {rule.outcome === 'FAIL' ? '\u2716 ' : '\u2713 '}
                  {rule.outcome}
                </span>
              </td>
              <td className="px-3 py-2 font-mono text-xs">{rule.reason_code}</td>
              <td className="px-3 py-2 font-mono text-xs">{rule.effect}</td>
              <td className="px-3 py-2 text-xs">{rule.precedence_rank}</td>
            </tr>
          ))}
        </Table>
      </Section>

      <Section title={t('progress.limits')}>
        <Table
          caption={t('progress.limits')}
          headers={[t('progress.limitKey'), t('progress.hardLimit'), t('progress.failureCode')]}
        >
          {limits.map((limit) => (
            <tr key={limit.key} className="border-b border-slate-100 last:border-b-0">
              <td className="px-3 py-2 font-mono text-xs">{limit.key}</td>
              <td className="px-3 py-2 text-sm">
                {limit.hard_limit} {limit.unit}
              </td>
              <td className="px-3 py-2 font-mono text-xs">{limit.failure_reason_code}</td>
            </tr>
          ))}
        </Table>
      </Section>
    </>
  );
}
