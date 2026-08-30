import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { usePacket, useSubmitDisposition } from '../api/hooks';
import type { DispositionValue } from '../api/types';
import { StatusIndicator } from '../components/StatusIndicator';
import {
  Button,
  Card,
  DataList,
  ErrorPanel,
  Loading,
  Mono,
  NoticeList,
  PageHeading,
  Section,
} from '../components/ui';
import { useSession } from '../features/session/SessionContext';
import { useLanguage } from '../i18n/LanguageProvider';
import type { MessageKey } from '../i18n/messages';

/**
 * The reviewer console.
 *
 * There is no approve action and no wording that suggests one. The three outcomes are
 * test-only, the rationale is mandatory, and the submitted disposition is bound to the
 * exact packet version and hash the reviewer was shown.
 */
const RATIONALE_MIN = 20;

const DISPOSITIONS: DispositionValue[] = [
  'RETURN_FOR_CLARIFICATION',
  'ACCEPT_AS_TEST_EVIDENCE',
  'REJECT_AS_TEST_EVIDENCE',
];

export function ReviewCasePage() {
  const { language, t } = useLanguage();
  const { caseId = '' } = useParams();
  const { me } = useSession();
  const packetQuery = usePacket(caseId);
  const submit = useSubmitDisposition();

  const [selected, setSelected] = useState<DispositionValue>('ACCEPT_AS_TEST_EVIDENCE');
  const [rationale, setRationale] = useState('');

  const rationaleOk = rationale.trim().length >= RATIONALE_MIN;

  if (packetQuery.isLoading) return <Loading />;
  if (packetQuery.error) {
    return (
      <>
        <PageHeading title={t('review.caseTitle')} />
        <ErrorPanel error={packetQuery.error} />
      </>
    );
  }
  if (!packetQuery.data) return null;

  const { packet, canonical_sha256: sha, seal_verified: sealVerified } = packetQuery.data;
  const selfReview = me?.identity_id === packet.request_context.requester_identity_id;

  return (
    <>
      <PageHeading
        title={t('review.caseTitle')}
        description={packet.request_context.normalised_question}
        actions={
          <Link className="text-sm underline hover:no-underline" to={`/cases/${caseId}/packet`}>
            {t('packet.title')}
          </Link>
        }
      />

      <Card className="mb-6">
        <StatusIndicator kind="review" withDetail />
      </Card>

      <Section title={t('review.revalidation')}>
        <Card>
          <DataList
            rows={[
              [
                'Seal',
                sealVerified ? (
                  <span key="ok">{'\u2713'} {t('packet.sealVerified')}</span>
                ) : (
                  <span key="no" className="font-semibold text-status-stop">
                    {'\u2716'} {t('packet.sealNotVerified')}
                  </span>
                ),
              ],
              ['SHA-256', <Mono key="s">{sha}</Mono>],
              [
                'Pre-issuance audit',
                <Mono key="a">{packet.audit_binding.pre_issuance_event_id ?? '—'}</Mono>,
              ],
              [
                'Material claims',
                `${packet.claim_ledger.filter((c) => c.materiality === 'MATERIAL' && c.support_state === 'SUPPORTED').length} supported of ${packet.claim_ledger.filter((c) => c.materiality === 'MATERIAL').length}`,
              ],
            ]}
          />
        </Card>
      </Section>

      <Section title={t('review.sod')}>
        <Card>
          {selfReview ? (
            <p className="text-sm font-semibold text-status-stop">
              {'\u2716'} You requested this case, so you cannot review it. The server will refuse
              any disposition you submit.
            </p>
          ) : (
            <p className="text-sm text-navy-deep">
              {'\u2713'} {t('review.sodPassed')}
            </p>
          )}
          <p className="mt-2 text-xs text-navy-slate">
            Requester: <Mono>{packet.request_context.requester_identity_id}</Mono>
            {' · '}You: <Mono>{me?.identity_id}</Mono>
          </p>
        </Card>
      </Section>

      <Section title={t('review.dispositionHeading')} description={t('review.dispositionExplain')}>
        {submit.error ? <ErrorPanel error={submit.error} /> : null}
        {submit.isSuccess ? (
          <div role="status" className="mb-4 rounded-lg border border-slate-300 bg-white p-4">
            <p className="text-sm font-semibold text-navy-deep">{t('review.recorded')}</p>
            <p className="mt-1 text-sm text-navy-slate">{submit.data.non_execution_notice}</p>
            <p className="mt-2 font-mono text-xs text-navy-slate">
              {submit.data.terminal_state} · closure {submit.data.closure_event_id}
            </p>
          </div>
        ) : null}

        <Card>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (rationaleOk && !submit.isPending) {
                submit.mutate({
                  caseId,
                  dispositionValue: selected,
                  rationale: rationale.trim(),
                  packetSha256: sha,
                });
              }
            }}
          >
            <fieldset>
              <legend className="text-sm font-semibold text-navy-deep">
                {t('review.dispositionHeading')}
              </legend>
              <div className="mt-3 space-y-2">
                {DISPOSITIONS.map((value) => (
                  <div key={value} className="flex items-start gap-3 text-sm">
                    <input
                      id={`disposition-${value}`}
                      type="radio"
                      name="disposition"
                      value={value}
                      checked={selected === value}
                      onChange={() => setSelected(value)}
                      className="mt-1"
                    />
                    <label htmlFor={`disposition-${value}`}>
                      <span className="font-medium text-navy-deep">
                        {t(`review.disposition.${value}` as MessageKey)}
                      </span>
                      <span className="ms-2 font-mono text-xs text-navy-slate">{value}</span>
                    </label>
                  </div>
                ))}
              </div>
            </fieldset>

            <div className="mt-5">
              <label htmlFor="rationale" className="block text-sm font-semibold text-navy-deep">
                {t('review.rationaleLabel')}
              </label>
              <p id="rationale-help" className="mt-1 max-w-prose text-sm text-navy-slate">
                {t('review.rationaleHelp')}
              </p>
              <textarea
                id="rationale"
                name="rationale"
                rows={4}
                value={rationale}
                onChange={(event) => setRationale(event.target.value)}
                aria-describedby="rationale-help rationale-count rationale-validation"
                aria-invalid={rationale.length > 0 && !rationaleOk}
                className="mt-2 w-full rounded-md border border-slate-300 p-3 text-sm leading-relaxed focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-nabd"
              />
              <p id="rationale-count" className="mt-1 text-xs text-navy-slate">
                {rationale.trim().length} / {RATIONALE_MIN} {t('newCase.charCount')}
              </p>
              <p
                id="rationale-validation"
                role="status"
                aria-live="polite"
                className="mt-1 min-h-5 text-sm"
              >
                {rationale.length > 0 && !rationaleOk ? (
                  <span className="font-medium text-status-stop">
                    {t('review.rationaleTooShort')}
                  </span>
                ) : null}
              </p>
            </div>

            <div className="mt-4">
              <Button type="submit" disabled={!rationaleOk || submit.isPending}>
                {submit.isPending ? `${t('review.submitting')}…` : t('review.submit')}
              </Button>
            </div>
          </form>
        </Card>
      </Section>

      <NoticeList notices={packet.notices} language={language} heading={t('packet.notices')} />
    </>
  );
}
