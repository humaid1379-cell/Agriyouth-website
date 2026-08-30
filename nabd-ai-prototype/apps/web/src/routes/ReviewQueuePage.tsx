import { Link } from 'react-router-dom';

import { useReviewQueue } from '../api/hooks';
import { StatusIndicator, statusKindFor } from '../components/StatusIndicator';
import { ErrorPanel, Loading, Mono, PageHeading, Table } from '../components/ui';
import { useSession } from '../features/session/SessionContext';
import { useTranslate } from '../i18n/LanguageProvider';

export function ReviewQueuePage() {
  const t = useTranslate();
  const { me } = useSession();
  const queue = useReviewQueue(me?.role === 'REVIEWER');

  if (me?.role !== 'REVIEWER') {
    return (
      <>
        <PageHeading title={t('review.title')} />
        <p className="text-sm text-navy-slate">{t('settings.notAdministrator')}</p>
      </>
    );
  }

  if (queue.isLoading) return <Loading />;
  if (queue.error) return <ErrorPanel error={queue.error} />;

  return (
    <>
      <PageHeading
        title={t('review.title')}
        description="Only packets you did not request, within your business scope, appear here."
      />
      {queue.data && queue.data.cases.length === 0 ? (
        <p className="py-8 text-sm text-navy-slate">{t('review.empty')}</p>
      ) : null}
      {queue.data && queue.data.cases.length > 0 ? (
        <Table caption={t('review.title')} headers={[t('cases.question'), t('cases.state'), t('cases.actions')]}>
          {queue.data.cases.map((item) => (
            <tr key={item.case_id} className="border-b border-slate-100 last:border-b-0">
              <td className="max-w-md px-3 py-3 align-top">
                <p className="line-clamp-3 text-sm text-navy-deep">{item.normalised_question}</p>
                <Mono>{item.case_id}</Mono>
              </td>
              <td className="px-3 py-3 align-top">
                <StatusIndicator kind={statusKindFor(item.current_state, item.route)} compact />
              </td>
              <td className="px-3 py-3 align-top">
                <Link className="text-sm underline hover:no-underline" to={`/review/${item.case_id}`}>
                  {t('review.open')}
                </Link>
              </td>
            </tr>
          ))}
        </Table>
      ) : null}
    </>
  );
}
