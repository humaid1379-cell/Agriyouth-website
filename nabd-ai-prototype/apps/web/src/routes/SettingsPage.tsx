import { useState } from 'react';

import { useConfiguration, useToggleKillSwitch } from '../api/hooks';
import {
  Button,
  Card,
  DataList,
  ErrorPanel,
  Loading,
  Mono,
  PageHeading,
  Section,
  StatusDimensions,
  Table,
} from '../components/ui';
import { useSession } from '../features/session/SessionContext';
import { useTranslate } from '../i18n/LanguageProvider';

const REASON_MIN = 10;

export function SettingsPage() {
  const t = useTranslate();
  const { me } = useSession();
  const isAdministrator = me?.role === 'ADMINISTRATOR';
  const configuration = useConfiguration(isAdministrator);
  const toggle = useToggleKillSwitch();
  const [reason, setReason] = useState('');

  if (!isAdministrator) {
    return (
      <>
        <PageHeading title={t('settings.title')} />
        <p className="text-sm text-navy-slate">{t('settings.notAdministrator')}</p>
      </>
    );
  }

  if (configuration.isLoading) return <Loading />;
  if (configuration.error) return <ErrorPanel error={configuration.error} />;
  if (!configuration.data) return null;

  const config = configuration.data;
  const reasonOk = reason.trim().length >= REASON_MIN;

  return (
    <>
      <PageHeading title={t('settings.title')} description={t('settings.cannotGrant')} />

      <Section title={t('assurance.statusHeading')}>
        <StatusDimensions
          status={config.status}
          labels={{
            built: t('assurance.built'),
            integration: t('assurance.integration'),
            operational: t('assurance.operational'),
            authorization: t('assurance.authorization'),
          }}
        />
      </Section>

      <Section title={t('settings.killSwitch')} description={t('settings.killSwitchExplain')}>
        {toggle.error ? <ErrorPanel error={toggle.error} /> : null}
        <Card>
          <div className="flex items-start gap-3">
            <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true" className="shrink-0">
              <path
                d="M8 2 H16 L22 8 V16 L16 22 H8 L2 16 V8 Z"
                fill="none"
                stroke={config.kill_switch.active ? '#A9474F' : '#133047'}
                strokeWidth="2"
                strokeLinejoin="round"
              />
              <path
                d="M7.5 12 H16.5"
                stroke={config.kill_switch.active ? '#A9474F' : '#133047'}
                strokeWidth="2.4"
                strokeLinecap="round"
              />
            </svg>
            <p
              className={
                config.kill_switch.active
                  ? 'font-semibold text-status-stop'
                  : 'font-semibold text-navy-deep'
              }
            >
              {config.kill_switch.active
                ? t('settings.killSwitchActive')
                : t('settings.killSwitchInactive')}
            </p>
          </div>

          {config.kill_switch.reason ? (
            <p className="mt-2 text-sm text-navy-slate">{config.kill_switch.reason}</p>
          ) : null}

          <form
            className="mt-4"
            onSubmit={(event) => {
              event.preventDefault();
              if (reasonOk && !toggle.isPending) {
                toggle.mutate(
                  { active: !config.kill_switch.active, reason: reason.trim() },
                  { onSuccess: () => setReason('') },
                );
              }
            }}
          >
            <label htmlFor="kill-reason" className="block text-sm font-semibold text-navy-deep">
              {t('settings.killSwitchReason')}
            </label>
            <input
              id="kill-reason"
              type="text"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              className="mt-2 w-full rounded-md border border-slate-300 p-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-nabd"
            />
            <div className="mt-3">
              <Button
                type="submit"
                variant={config.kill_switch.active ? 'secondary' : 'caution'}
                disabled={!reasonOk || toggle.isPending}
              >
                {config.kill_switch.active ? t('settings.release') : t('settings.engage')}
              </Button>
            </div>
          </form>
        </Card>
      </Section>

      <Section title={t('settings.versions')}>
        <Card>
          <DataList
            rows={[
              ...Object.entries(config.component_versions).map(
                ([key, value]) => [key, <Mono key={key}>{value}</Mono>] as [string, React.ReactNode],
              ),
              [t('settings.corpusHash'), <Mono key="c">{config.corpus_manifest_sha256}</Mono>],
            ]}
          />
        </Card>
      </Section>

      <Section title={t('settings.rules')}>
        <Table
          caption={t('settings.rules')}
          headers={['Rule', 'Version', 'Precedence', 'Purpose']}
        >
          {config.rule_catalog.map((rule) => (
            <tr key={rule.rule_id} className="border-b border-slate-100 last:border-b-0">
              <td className="px-3 py-2 font-mono text-xs font-semibold">{rule.rule_id}</td>
              <td className="px-3 py-2 font-mono text-xs">{rule.rule_version}</td>
              <td className="px-3 py-2 text-xs">{rule.precedence_rank}</td>
              <td className="max-w-lg px-3 py-2 text-xs text-navy-slate">{rule.purpose}</td>
            </tr>
          ))}
        </Table>
      </Section>

      <Section title={t('settings.limits')}>
        <Table caption={t('settings.limits')} headers={['Resource', 'Hard limit', 'Failure code']}>
          {config.limits.map((limit) => (
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

      <Section title={t('settings.stateMachine')}>
        <Table
          caption={t('settings.stateMachine')}
          headers={['Stage', 'State', 'Permitted next', 'Failure code']}
        >
          {config.state_machine.map((row) => (
            <tr key={row.state} className="border-b border-slate-100 last:border-b-0">
              <td className="px-3 py-2 text-xs">{row.stage ?? '—'}</td>
              <td className="px-3 py-2 font-mono text-xs font-semibold">{row.state}</td>
              <td className="px-3 py-2 font-mono text-[0.65rem] text-navy-slate">
                {row.permitted_next_states.join(', ') || '—'}
              </td>
              <td className="px-3 py-2 font-mono text-[0.65rem]">{row.failure_reason_code ?? '—'}</td>
            </tr>
          ))}
        </Table>
      </Section>

      <Section title={t('settings.prohibited')}>
        <Table
          caption={t('settings.prohibited')}
          headers={['ID', 'Category', 'Enforcement', 'Status']}
        >
          {config.prohibited_integrations.map((entry) => (
            <tr key={entry.integration_id} className="border-b border-slate-100 last:border-b-0">
              <td className="px-3 py-2 font-mono text-xs">{entry.integration_id}</td>
              <td className="px-3 py-2 text-xs">{entry.category}</td>
              <td className="px-3 py-2 text-xs text-navy-slate">{entry.enforcement}</td>
              <td className="px-3 py-2 font-mono text-xs">{entry.status}</td>
            </tr>
          ))}
        </Table>
      </Section>

      <Section title={t('settings.models')}>
        <Table
          caption={t('settings.models')}
          headers={['Configuration', 'Role', 'Revision', 'Tools', 'Fallback']}
        >
          {config.model_configurations.map((model, index) => (
            <tr key={index} className="border-b border-slate-100 last:border-b-0">
              <td className="px-3 py-2 font-mono text-xs">
                {String(model.model_configuration_id ?? '')}
              </td>
              <td className="px-3 py-2 font-mono text-xs">{String(model.task_role ?? '')}</td>
              <td className="px-3 py-2 font-mono text-xs">{String(model.model_revision ?? '')}</td>
              <td className="px-3 py-2 font-mono text-xs">
                {model.tool_calling_enabled ? 'ENABLED' : 'DISABLED'}
              </td>
              <td className="px-3 py-2 font-mono text-xs">
                {model.fallback_enabled ? 'ENABLED' : 'DISABLED'}
              </td>
            </tr>
          ))}
        </Table>
      </Section>
    </>
  );
}
