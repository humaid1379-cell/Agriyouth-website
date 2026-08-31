import { Link, useParams } from 'react-router-dom';

import { usePacket } from '../api/hooks';
import { StatusIndicator } from '../components/StatusIndicator';
import {
  Badge,
  Button,
  Card,
  Collapsible,
  DataList,
  ErrorPanel,
  Loading,
  Mono,
  NoticeList,
  PageHeading,
  Section,
  StatusDimensions,
  Table,
} from '../components/ui';
import { useLanguage } from '../i18n/LanguageProvider';

const SUPPORT_MARK: Record<string, string> = {
  SUPPORTED: '\u2713',
  PARTIALLY_SUPPORTED: '\u25D1',
  UNSUPPORTED: '\u2716',
  CONFLICTED: '\u26A0',
  NOT_APPLICABLE: '\u2014',
};

export function PacketPage() {
  const { language, t } = useLanguage();
  const { caseId = '' } = useParams();
  const packetQuery = usePacket(caseId);

  if (packetQuery.isLoading) return <Loading />;
  if (packetQuery.error) {
    return (
      <>
        <PageHeading title={t('packet.title')} />
        <p className="mb-4 max-w-prose text-sm text-navy-slate">{t('packet.notAvailable')}</p>
        <ErrorPanel error={packetQuery.error} />
      </>
    );
  }
  if (!packetQuery.data) return null;

  const { packet, canonical_sha256: sha, seal_verified: sealVerified } = packetQuery.data;

  return (
    <>
      <PageHeading
        title={t('packet.title')}
        description={t('packet.derivedRenderingNote')}
        actions={
          <Button variant="secondary" onClick={() => window.print()} className="no-print">
            {t('packet.print')}
          </Button>
        }
      />

      <Card className="mb-6">
        <StatusIndicator kind="review" withDetail />
        <div className="mt-4">
          <DataList
            rows={[
              [t('packet.question'), packet.request_context.normalised_question],
              [t('packet.route'), <Mono key="route">{packet.route}</Mono>],
              ['Packet', <Mono key="pid">{`${packet.identity.packet_id} v${packet.identity.packet_version}`}</Mono>],
              [t('app.environment'), <Mono key="env">{packet.identity.environment_id}</Mono>],
            ]}
          />
        </div>
      </Card>

      <Section title={t('packet.claims')}>
        <ul className="space-y-4">
          {packet.claim_ledger.map((claim) => (
            <li key={claim.claim_id}>
              <Card>
                <div className="flex flex-wrap items-baseline gap-2">
                  <span className="font-mono text-sm font-semibold text-navy-deep">
                    {claim.claim_ref}
                  </span>
                  <Badge tone={claim.materiality === 'MATERIAL' ? 'warn' : 'neutral'}>
                    {claim.materiality}
                  </Badge>
                  <span className="font-mono text-xs text-navy-slate">
                    {SUPPORT_MARK[claim.support_state] ?? ''} {claim.support_state}
                  </span>
                </div>
                <p className="mt-2 max-w-prose text-sm leading-relaxed text-navy-deep">
                  {claim.statement}
                </p>
                {claim.qualification ? (
                  <p className="mt-2 max-w-prose text-sm text-status-review">
                    {claim.qualification}
                  </p>
                ) : null}

                <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-navy-slate">
                  {t('packet.citations')}
                </p>
                <ul className="mt-1 space-y-1">
                  {claim.evidence_links.map((link) => (
                    <li key={link.excerpt_id} className="text-sm">
                      <Link
                        className="underline hover:no-underline"
                        to={`/cases/${caseId}/evidence/${link.excerpt_id}`}
                      >
                        {link.source_id}@{link.source_version} · {t('evidence.page')}{' '}
                        {link.page_number} · [{link.char_start}–{link.char_end}]
                      </Link>
                      {link.quote_verified ? (
                        <span className="ms-2 text-xs text-navy-slate">
                          {'\u2713'} quote re-verified against the stored passage
                        </span>
                      ) : (
                        <span className="ms-2 text-xs font-semibold text-status-stop">
                          {'\u2716'} quote did not reproduce
                        </span>
                      )}
                      <blockquote className="mt-1 border-s-2 border-slate-300 ps-3 text-xs italic text-navy-slate">
                        {link.quoted_text}
                      </blockquote>
                    </li>
                  ))}
                </ul>
              </Card>
            </li>
          ))}
        </ul>
      </Section>

      <Section title={t('packet.risk')}>
        <Card>
          <DataList
            rows={[
              ['Inherent risk', <Mono key="r">{packet.risk.inherent_risk}</Mono>],
              [t('packet.dominantFactor'), <Mono key="d">{packet.risk.dominant_factor_id}</Mono>],
              [t('packet.reviewerSeniority'), packet.risk.reviewer_seniority_required],
              [t('packet.reviewDepth'), packet.risk.review_depth_required],
              ['Method', <Mono key="m">{packet.risk.method}</Mono>],
            ]}
          />
          <ul className="mt-4 space-y-2">
            {packet.risk.factors.map((factor) => (
              <li key={factor.factor_id} className="text-sm">
                <span className="font-medium text-navy-deep">
                  {language === 'ar' && factor.label_ar ? factor.label_ar : factor.label_en}
                </span>
                <span className="ms-2 font-mono text-xs text-navy-slate">{factor.level}</span>
                <p className="text-xs text-navy-slate">{factor.rationale}</p>
              </li>
            ))}
          </ul>
        </Card>
      </Section>

      <Section title={t('packet.uncertainty')}>
        {packet.uncertainty.length === 0 && packet.conflicts.length === 0 ? (
          <p className="text-sm text-navy-slate">{t('packet.noUncertainty')}</p>
        ) : (
          <ul className="space-y-3">
            {packet.uncertainty.map((record) => (
              <li key={record.uncertainty_id}>
                <Card>
                  <p className="font-mono text-xs text-navy-slate">{record.kind}</p>
                  <p className="mt-1 max-w-prose text-sm text-navy-deep">
                    {language === 'ar' && record.description_ar
                      ? record.description_ar
                      : record.description_en}
                  </p>
                  {record.affected_source_ids.length > 0 ? (
                    <p className="mt-1 font-mono text-xs text-navy-slate">
                      {record.affected_source_ids.join(', ')}
                    </p>
                  ) : null}
                </Card>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section
        title={t('packet.rules')}
        description={`${packet.rule_results.length} evaluations, ${
          packet.rule_results.filter((rule) => rule.outcome === 'FAIL').length
        } failing. Every evaluation is retained in the packet; the full list is collapsed for readability.`}
      >
        <Collapsible
          summary={`${t('packet.rules')} (${packet.rule_results.length})`}
          defaultOpen={packet.rule_results.some((rule) => rule.outcome === 'FAIL')}
        >
          <Table caption={t('packet.rules')} headers={['Rule', 'Outcome', 'Reason', 'Effect']}>
            {packet.rule_results.map((rule, index) => (
              <tr
                key={`${rule.rule_id}-${index}`}
                className="border-b border-slate-100 last:border-b-0"
              >
                <td className="px-3 py-2 font-mono text-xs">{rule.rule_id}</td>
                <td
                  className={
                    rule.outcome === 'FAIL'
                      ? 'px-3 py-2 text-xs font-semibold text-status-stop'
                      : 'px-3 py-2 text-xs'
                  }
                >
                  {rule.outcome}
                </td>
                <td className="px-3 py-2 font-mono text-xs">{rule.reason_code}</td>
                <td className="px-3 py-2 font-mono text-xs">{rule.effect}</td>
              </tr>
            ))}
          </Table>
        </Collapsible>
      </Section>

      <Section title={t('packet.integrity')}>
        <Card>
          <DataList
            rows={[
              ['SHA-256', <Mono key="s">{sha}</Mono>],
              ['Profile', <Mono key="p">{packet.integrity.canonical_json_profile}</Mono>],
              ['Verifier method', <Mono key="v">{packet.integrity.verifier_method}</Mono>],
              [
                'Seal',
                sealVerified ? (
                  <span key="ok" className="text-sm">
                    {'\u2713'} {t('packet.sealVerified')}
                  </span>
                ) : (
                  <span key="no" className="text-sm font-semibold text-status-stop">
                    {'\u2716'} {t('packet.sealNotVerified')}
                  </span>
                ),
              ],
              [
                'Pre-issuance audit',
                <Mono key="a">{packet.audit_binding.pre_issuance_event_id ?? '—'}</Mono>,
              ],
              [
                'Closure audit',
                <Mono key="c">{packet.audit_binding.disposition_closure_event_id ?? '—'}</Mono>,
              ],
            ]}
          />
          <p className="mt-3 max-w-prose text-xs leading-relaxed text-navy-slate">
            {packet.integrity.tamper_evidence_note}
          </p>
        </Card>
      </Section>

      <Section title={t('packet.lineageVersions')}>
        <Card>
          <DataList
            rows={Object.entries(packet.version_lineage).map(([key, value]) => [
              key,
              <Mono key={key}>{value}</Mono>,
            ])}
          />
        </Card>
      </Section>

      <Section title={t('packet.limitations')}>
        <ul className="list-disc space-y-1 ps-5 text-sm text-navy-deep">
          {packet.limitations.map((limitation) => (
            <li key={limitation} className="max-w-prose">
              {limitation}
            </li>
          ))}
        </ul>
      </Section>

      {packet.disposition ? (
        <Section title={t('packet.disposition')}>
          <Card>
            <DataList
              rows={[
                ['Outcome', <Mono key="o">{packet.disposition.disposition_value}</Mono>],
                ['Reviewer', <Mono key="r">{packet.disposition.reviewer_identity_id}</Mono>],
                ['Rationale', packet.disposition.human_rationale],
              ]}
            />
            <p className="mt-3 max-w-prose rounded border border-violet-authority/30 bg-violet-authority/5 p-3 text-xs text-navy-deep">
              {packet.disposition.non_execution_notice}
            </p>
          </Card>
        </Section>
      ) : null}

      <NoticeList notices={packet.notices} language={language} heading={t('packet.notices')} />

      <Section title={t('packet.status')}>
        <StatusDimensions
          status={packet.prototype_status}
          labels={{
            built: t('assurance.built'),
            integration: t('assurance.integration'),
            operational: t('assurance.operational'),
            authorization: t('assurance.authorization'),
          }}
        />
      </Section>
    </>
  );
}
