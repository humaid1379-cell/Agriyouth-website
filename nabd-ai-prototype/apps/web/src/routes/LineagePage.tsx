import { useParams } from 'react-router-dom';

import { useLineage } from '../api/hooks';
import { Card, ErrorPanel, Loading, Mono, PageHeading, Section } from '../components/ui';
import { useTranslate } from '../i18n/LanguageProvider';
import type { MessageKey } from '../i18n/messages';

const ORDER = ['SOURCE', 'EXCERPT', 'CLAIM', 'RULE', 'ROUTE', 'PACKET'] as const;

export function LineagePage() {
  const t = useTranslate();
  const { caseId = '' } = useParams();
  const lineage = useLineage(caseId);

  if (lineage.isLoading) return <Loading />;
  if (lineage.error) return <ErrorPanel error={lineage.error} />;
  if (!lineage.data) return null;

  const { nodes, edges } = lineage.data;
  const labelFor = (id: string) => nodes.find((node) => node.node_id === id)?.label ?? id;

  return (
    <>
      <PageHeading title={t('lineage.title')} description={t('lineage.explain')} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {ORDER.map((kind) => {
          const group = nodes.filter((node) => node.kind === kind);
          if (group.length === 0) return null;
          return (
            <Card key={kind}>
              <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-navy-slate">
                {t(`lineage.${kind}` as MessageKey)} ({group.length})
              </h2>
              <ul className="space-y-2">
                {group.map((node) => (
                  <li key={node.node_id} className="rounded border border-slate-200 p-2">
                    <p className="text-sm font-medium text-navy-deep">{node.label}</p>
                    {node.detail ? <p className="text-xs text-navy-slate">{node.detail}</p> : null}
                  </li>
                ))}
              </ul>
            </Card>
          );
        })}
      </div>

      <Section title={t('lineage.relations')}>
        <ul className="space-y-1 text-sm">
          {edges.map((edge, index) => (
            <li key={`${edge.source}-${edge.target}-${index}`} className="flex flex-wrap gap-2">
              <Mono>{labelFor(edge.source)}</Mono>
              <span className="text-navy-slate">{'\u2192'}</span>
              <span className="font-mono text-xs text-violet-authority">{edge.relation}</span>
              <span className="text-navy-slate">{'\u2192'}</span>
              <Mono>{labelFor(edge.target)}</Mono>
            </li>
          ))}
        </ul>
      </Section>
    </>
  );
}
