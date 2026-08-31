import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { request } from './client';
import {
  auditResponseSchema,
  caseListSchema,
  caseSummarySchema,
  configurationSchema,
  demoIdentitySchema,
  dispositionResponseSchema,
  excerptSchema,
  killSwitchSchema,
  lineageSchema,
  meSchema,
  packetResponseSchema,
  progressSchema,
  sessionSchema,
  sourcePageSchema,
  tevvRunSchema,
  useCaseSchema,
  type DispositionValue,
} from './types';
import { z } from 'zod';

export const queryKeys = {
  identities: ['demo-identities'] as const,
  me: ['me'] as const,
  useCase: ['use-case'] as const,
  cases: ['cases'] as const,
  case: (id: string) => ['case', id] as const,
  progress: (id: string) => ['progress', id] as const,
  packet: (id: string) => ['packet', id] as const,
  excerpt: (id: string) => ['excerpt', id] as const,
  sourcePage: (source: string, page: number) => ['source-page', source, page] as const,
  audit: (id: string) => ['audit', id] as const,
  lineage: (id: string) => ['lineage', id] as const,
  reviewQueue: ['review-queue'] as const,
  configuration: ['configuration'] as const,
  tevvRun: (id: string) => ['tevv-run', id] as const,
};

export function useDemoIdentities() {
  return useQuery({
    queryKey: queryKeys.identities,
    queryFn: () => request('/api/v1/demo/identities', z.array(demoIdentitySchema), { token: null }),
  });
}

export function useMe(enabled: boolean) {
  return useQuery({ queryKey: queryKeys.me, queryFn: () => request('/api/v1/me', meSchema), enabled });
}

export function useUseCase(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.useCase,
    queryFn: () => request('/api/v1/use-case', useCaseSchema),
    enabled,
  });
}

export function useCreateSession() {
  return useMutation({
    mutationFn: (identityId: string) =>
      request('/api/v1/demo/session', sessionSchema, {
        method: 'POST',
        body: { identity_id: identityId },
        token: null,
      }),
  });
}

export function useCases(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.cases,
    queryFn: () => request('/api/v1/cases', caseListSchema),
    enabled,
  });
}

export function useCase(caseId: string) {
  return useQuery({
    queryKey: queryKeys.case(caseId),
    queryFn: () => request(`/api/v1/cases/${caseId}`, caseSummarySchema),
  });
}

export function useProgress(caseId: string) {
  return useQuery({
    queryKey: queryKeys.progress(caseId),
    queryFn: () => request(`/api/v1/cases/${caseId}/progress`, progressSchema),
  });
}

export function usePacket(caseId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.packet(caseId),
    queryFn: () => request(`/api/v1/cases/${caseId}/packet`, packetResponseSchema),
    enabled,
    retry: false,
  });
}

export function useExcerpt(excerptId: string) {
  return useQuery({
    queryKey: queryKeys.excerpt(excerptId),
    queryFn: () => request(`/api/v1/evidence/${excerptId}`, excerptSchema),
  });
}

export function useSourcePage(sourceId: string, page: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.sourcePage(sourceId, page),
    queryFn: () => request(`/api/v1/sources/${sourceId}/pages/${page}`, sourcePageSchema),
    enabled,
    retry: false,
  });
}

export function useAudit(caseId: string) {
  return useQuery({
    queryKey: queryKeys.audit(caseId),
    queryFn: () => request(`/api/v1/cases/${caseId}/audit`, auditResponseSchema),
  });
}

export function useLineage(caseId: string) {
  return useQuery({
    queryKey: queryKeys.lineage(caseId),
    queryFn: () => request(`/api/v1/cases/${caseId}/lineage`, lineageSchema),
  });
}

export function useReviewQueue(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.reviewQueue,
    queryFn: () => request('/api/v1/review/queue', caseListSchema),
    enabled,
  });
}

export function useConfiguration(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.configuration,
    queryFn: () => request('/api/v1/admin/configuration', configurationSchema),
    enabled,
    retry: false,
  });
}

export function useCreateCase() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (question: string) =>
      request('/api/v1/cases', caseSummarySchema, { method: 'POST', body: { question } }),
    onSuccess: () => void client.invalidateQueries({ queryKey: queryKeys.cases }),
  });
}

export function useProcessCase() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (caseId: string) =>
      request(`/api/v1/cases/${caseId}/process`, caseSummarySchema, { method: 'POST' }),
    onSuccess: (summary) => {
      void client.invalidateQueries({ queryKey: queryKeys.cases });
      void client.invalidateQueries({ queryKey: queryKeys.case(summary.case_id) });
    },
  });
}

export interface DispositionInput {
  caseId: string;
  dispositionValue: DispositionValue;
  rationale: string;
  packetSha256?: string;
}

export function useSubmitDisposition() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: DispositionInput) =>
      request(`/api/v1/cases/${input.caseId}/dispositions`, dispositionResponseSchema, {
        method: 'POST',
        body: {
          disposition_value: input.dispositionValue,
          human_rationale: input.rationale,
          ...(input.packetSha256 ? { packet_sha256: input.packetSha256 } : {}),
        },
      }),
    onSuccess: (result) => {
      void client.invalidateQueries({ queryKey: queryKeys.reviewQueue });
      void client.invalidateQueries({ queryKey: queryKeys.case(result.case_id) });
      void client.invalidateQueries({ queryKey: queryKeys.packet(result.case_id) });
      void client.invalidateQueries({ queryKey: queryKeys.audit(result.case_id) });
    },
  });
}

export function useToggleKillSwitch() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { active: boolean; reason: string }) =>
      request('/api/v1/admin/kill-switch', killSwitchSchema, { method: 'POST', body: input }),
    onSuccess: () => void client.invalidateQueries({ queryKey: queryKeys.configuration }),
  });
}

export function useRunTevv() {
  return useMutation({
    mutationFn: (scenarioIds: string[]) =>
      request('/api/v1/admin/tevv/run', tevvRunSchema, {
        method: 'POST',
        body: { scenario_ids: scenarioIds },
      }),
  });
}

export function useVerifyAudit() {
  return useMutation({
    mutationFn: (caseId: string | null) =>
      request(
        '/api/v1/admin/audit/verify',
        z.object({ verified: z.boolean(), event_count: z.number() }).passthrough(),
        { method: 'POST', body: { case_id: caseId } },
      ),
  });
}
