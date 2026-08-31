import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useCreateCase, useProcessCase, useUseCase } from '../api/hooks';
import { Badge, Button, Card, ErrorPanel, PageHeading, Section } from '../components/ui';
import { useSession } from '../features/session/SessionContext';
import { useLanguage } from '../i18n/LanguageProvider';
import type { MessageKey } from '../i18n/messages';
import type { UseCase } from '../api/types';

/**
 * Requester intake.
 *
 * The client checks mirror the server contract so a requester gets immediate feedback, but
 * they are advisory: the server re-applies REQ-001 and SCOPE-001 and its decision governs.
 * That is stated on the screen rather than left implied.
 */
function clientValidate(question: string, contract: UseCase | undefined): MessageKey | null {
  if (contract === undefined) return null;
  const trimmed = question.trim();
  if (trimmed.length < contract.min_question_chars) return 'newCase.errorTooShort';
  if (trimmed.length > contract.max_question_chars) return 'newCase.errorTooLong';
  if ((trimmed.match(/\?/g) ?? []).length > 1) return 'newCase.errorMultiple';
  const lowered = trimmed.toLowerCase();
  if (contract.excluded_scope_terms.some((term) => lowered.includes(term.toLowerCase()))) {
    return 'newCase.errorExcluded';
  }
  return null;
}

export function NewCasePage() {
  const { language, t } = useLanguage();
  const { me } = useSession();
  const navigate = useNavigate();
  const contract = useUseCase(me !== undefined);
  const createCase = useCreateCase();
  const processCase = useProcessCase();
  const [question, setQuestion] = useState('');

  const validationKey = useMemo(
    () => clientValidate(question, contract.data),
    [question, contract.data],
  );
  const touched = question.trim().length > 0;
  const blocked = validationKey !== null;
  const busy = createCase.isPending || processCase.isPending;

  function submit() {
    createCase.mutate(question.trim(), {
      onSuccess: (created) => {
        processCase.mutate(created.case_id, {
          onSettled: () => navigate(`/cases/${created.case_id}/progress`),
        });
      },
    });
  }

  return (
    <>
      <PageHeading
        title={t('newCase.title')}
        description={
          contract.data
            ? language === 'ar'
              ? contract.data.description_ar
              : contract.data.description_en
            : undefined
        }
      />

      {createCase.error ? <ErrorPanel error={createCase.error} /> : null}
      {processCase.error ? <ErrorPanel error={processCase.error} /> : null}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[2fr_1fr]">
        <Card>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!blocked && !busy) submit();
            }}
          >
            <label htmlFor="question" className="block text-sm font-semibold text-navy-deep">
              {t('newCase.questionLabel')}
            </label>
            <p id="question-help" className="mt-1 text-sm text-navy-slate">
              {t('newCase.questionHelp')}
            </p>
            <textarea
              id="question"
              name="question"
              rows={6}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              aria-describedby="question-help question-count question-validation"
              aria-invalid={touched && blocked}
              className="mt-3 w-full rounded-md border border-slate-300 p-3 text-sm leading-relaxed focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-nabd"
            />
            <p id="question-count" className="mt-1 text-xs text-navy-slate">
              {question.trim().length} / {contract.data?.max_question_chars ?? 2000}{' '}
              {t('newCase.charCount')}
            </p>

            <p id="question-validation" role="status" aria-live="polite" className="mt-2 min-h-5 text-sm">
              {touched && validationKey ? (
                <span className="font-medium text-status-stop">{t(validationKey)}</span>
              ) : null}
            </p>

            <p className="mt-3 max-w-prose rounded-md border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-navy-slate">
              {t('newCase.clientValidationNote')}
            </p>

            <div className="mt-4">
              <Button type="submit" disabled={blocked || busy || question.trim().length === 0}>
                {busy ? `${t('app.loading')}…` : t('newCase.process')}
              </Button>
            </div>
          </form>
        </Card>

        <aside>
          <Section title={t('newCase.contract')}>
            {contract.data ? (
              <div className="space-y-4 text-sm">
                <p className="font-mono text-xs text-navy-slate">
                  {contract.data.use_case_contract_id}
                </p>
                <div>
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-navy-slate">
                    {t('newCase.excludedTerms')}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {contract.data.excluded_scope_terms.slice(0, 16).map((term) => (
                      <Badge key={term}>{term}</Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-navy-slate">
                    {t('newCase.excludedOutcomes')}
                  </p>
                  <ul className="list-disc space-y-0.5 ps-5 font-mono text-xs text-navy-deep">
                    {contract.data.excluded_outcomes.map((outcome) => (
                      <li key={outcome}>{outcome}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}
          </Section>
        </aside>
      </div>
    </>
  );
}
