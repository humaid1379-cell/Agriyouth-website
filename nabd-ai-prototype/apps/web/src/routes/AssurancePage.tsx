import { useRunTevv } from '../api/hooks';
import {
  Button,
  Card,
  ErrorPanel,
  Mono,
  PageHeading,
  Section,
  StatusDimensions,
  Table,
} from '../components/ui';
import { useSession } from '../features/session/SessionContext';
import { useTranslate } from '../i18n/LanguageProvider';

const STATUS_MARK: Record<string, string> = {
  PASS: '\u2713',
  FAIL: '\u2716',
  BLOCKED: '\u26A0',
  NOT_RUN: '\u2014',
};

export function AssurancePage() {
  const t = useTranslate();
  const { me } = useSession();
  const runTevv = useRunTevv();
  const isAdministrator = me?.role === 'ADMINISTRATOR';

  const summary = runTevv.data?.summary as Record<string, unknown> | undefined;

  return (
    <>
      <PageHeading
        title={t('assurance.title')}
        description={t('assurance.statusExplain')}
      />

      <Section title={t('assurance.statusHeading')}>
        <StatusDimensions
          status={{
            built: 'NOT_EVIDENCED',
            integration: 'NOT_EVIDENCED',
            operational: 'NOT_EVIDENCED',
            authorization: 'NOT_GRANTED',
          }}
          labels={{
            built: t('assurance.built'),
            integration: t('assurance.integration'),
            operational: t('assurance.operational'),
            authorization: t('assurance.authorization'),
          }}
        />
      </Section>

      <Section title={t('assurance.tevv')}>
        {!isAdministrator ? (
          <p className="max-w-prose text-sm text-navy-slate">{t('assurance.notAdministrator')}</p>
        ) : (
          <>
            <Button onClick={() => runTevv.mutate([])} disabled={runTevv.isPending}>
              {runTevv.isPending ? `${t('assurance.running')}…` : t('assurance.runTevv')}
            </Button>
            {runTevv.error ? <ErrorPanel error={runTevv.error} /> : null}

            {runTevv.data ? (
              <>
                <Card className="my-4">
                  <p className="font-mono text-xs text-navy-slate">{runTevv.data.tevv_run_id}</p>
                  <p className="mt-2 text-sm text-navy-deep">
                    {t('assurance.numerator')}:{' '}
                    <span className="font-mono font-semibold">
                      {String(summary?.numerator_pass ?? '—')} / {String(summary?.denominator ?? '—')}
                    </span>
                    {' · '}failed <Mono>{String(summary?.failed ?? '—')}</Mono>
                    {' · '}blocked <Mono>{String(summary?.blocked ?? '—')}</Mono>
                    {' · '}not run <Mono>{String(summary?.not_run ?? '—')}</Mono>
                  </p>
                  {typeof summary?.benign_case_denominator_note === 'string' ? (
                    <p className="mt-3 max-w-prose rounded border border-status-review/40 bg-status-review/5 p-3 text-xs leading-relaxed text-navy-deep">
                      {summary.benign_case_denominator_note}
                    </p>
                  ) : null}
                  {typeof summary?.labelled_claim_coverage_note === 'string' ? (
                    <p className="mt-2 max-w-prose rounded border border-status-review/40 bg-status-review/5 p-3 text-xs leading-relaxed text-navy-deep">
                      {summary.labelled_claim_coverage_note}
                    </p>
                  ) : null}
                </Card>

                <Table
                  caption={t('assurance.tevv')}
                  headers={[
                    t('assurance.scenario'),
                    t('assurance.status'),
                    t('assurance.expected'),
                    t('assurance.actual'),
                    t('assurance.trace'),
                  ]}
                >
                  {runTevv.data.results.map((result) => (
                    <tr key={result.scenario_id} className="border-b border-slate-100 last:border-b-0">
                      <td className="px-3 py-2 align-top">
                        <p className="font-mono text-xs font-semibold">{result.scenario_id}</p>
                        <p className="text-xs text-navy-slate">{result.title}</p>
                      </td>
                      <td className="px-3 py-2 align-top">
                        <span
                          className={
                            result.status === 'PASS'
                              ? 'font-mono text-xs'
                              : 'font-mono text-xs font-semibold text-status-stop'
                          }
                        >
                          {STATUS_MARK[result.status] ?? ''} {result.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 align-top font-mono text-[0.65rem] text-navy-slate">
                        {String(result.expected.terminal_state ?? '')} /{' '}
                        {String(result.expected.reason_code ?? '—')}
                      </td>
                      <td className="px-3 py-2 align-top font-mono text-[0.65rem] text-navy-slate">
                        {String(result.actual.terminal_state ?? '')} /{' '}
                        {String(result.actual.reason_code ?? '—')}
                      </td>
                      <td className="px-3 py-2 align-top font-mono text-[0.6rem] text-navy-slate">
                        {result.trace_id.slice(0, 16)}…
                      </td>
                    </tr>
                  ))}
                </Table>
              </>
            ) : null}
          </>
        )}
      </Section>

      <Section title={t('assurance.defects')}>
        <p className="max-w-prose text-sm text-navy-slate">
          {runTevv.data && runTevv.data.results.every((result) => result.defect_ids.length === 0)
            ? t('assurance.noDefects')
            : 'Defects are recorded in artifacts/templates/defect_register.csv and linked from each TEVV result.'}
        </p>
      </Section>

      <Section title={t('assurance.evidence')}>
        <p className="max-w-prose text-sm leading-relaxed text-navy-slate">
          {t('assurance.evidenceExplain')}
        </p>
      </Section>
    </>
  );
}
