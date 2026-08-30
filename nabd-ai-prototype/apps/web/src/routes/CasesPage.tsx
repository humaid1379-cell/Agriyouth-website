import { Link } from 'react-router-dom';

import { useCases } from '../api/hooks';
import { StatusIndicator, statusKindFor } from '../components/StatusIndicator';
import { ErrorPanel, Loading, Mono, PageHeading, Table } from '../components/ui';
import { useSession } from '../features/session/SessionContext';
import { useTranslate } from '../i18n/LanguageProvider';

export function CasesPage() {
  const t = useTranslate();
  const { me } = useSession();
  const cases = useCases(me !== undefined);

  return (
    <>
      <PageHeading
        title={t('cases.title')}
        description={
          me?.role === 'REQUESTER'
            ? 'Cases you created. A reviewer sees a different, non-overlapping set.'
            : 'Cases within your business scope that you did not request.'
        }
      />

      {cases.isLoading ? <Loading /> : null}
      {cases.error ? <ErrorPanel error={cases.error} /> : null}

      {cases.data && cases.data.cases.length === 0 ? (
        <p className="py-8 text-sm text-navy-slate">{t('cases.empty')}</p>
      ) : null}

      {cases.data && cases.data.cases.length > 0 ? (
        <Table
          caption={t('cases.title')}
          headers={[
            t('cases.question'),
            t('cases.state'),
            t('cases.updated'),
            t('cases.actions'),
          ]}
        >
          {cases.data.cases.map((item) => (
            <tr key={item.case_id} className="border-b border-slate-100 last:border-b-0">
              <td className="max-w-md px-3 py-3 align-top">
                <p className="line-clamp-3 text-sm text-navy-deep">{item.normalised_question}</p>
                <Mono>{item.case_id}</Mono>
              </td>
              <td className="px-3 py-3 align-top">
                <StatusIndicator
                  kind={statusKindFor(item.current_state, item.route)}
                  compact
                  suffix={item.current_state}
                />
                {item.reason_message ? (
                  <p className="mt-1 max-w-xs text-xs text-navy-slate">{item.reason_message}</p>
                ) : null}
              </td>
              <td className="whitespace-nowrap px-3 py-3 align-top text-xs text-navy-slate">
                {new Date(item.updated_at).toISOString().replace('T', ' ').slice(0, 19)}Z
              </td>
              <td className="px-3 py-3 align-top">
                <ul className="flex flex-col gap-1 text-sm">
                  <li>
                    <Link className="underline hover:no-underline" to={`/cases/${item.case_id}/progress`}>
                      {t('cases.viewProgress')}
                    </Link>
                  </li>
                  {item.packet_available ? (
                    <li>
                      <Link className="underline hover:no-underline" to={`/cases/${item.case_id}/packet`}>
                        {t('cases.viewPacket')}
                      </Link>
                    </li>
                  ) : null}
                  <li>
                    <Link className="underline hover:no-underline" to={`/cases/${item.case_id}/audit`}>
                      {t('cases.viewAudit')}
                    </Link>
                  </li>
                  <li>
                    <Link className="underline hover:no-underline" to={`/cases/${item.case_id}/lineage`}>
                      {t('cases.viewLineage')}
                    </Link>
                  </li>
                </ul>
              </td>
            </tr>
          ))}
        </Table>
      ) : null}
    </>
  );
}
