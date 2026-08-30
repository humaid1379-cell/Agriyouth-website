import { z } from 'zod';

/**
 * Runtime-validated views of the API contract in `contracts/openapi.json`.
 *
 * The browser parses every response rather than trusting its shape. A response that does
 * not match is surfaced as an error, not rendered as if it were valid.
 */

export const routeSchema = z.enum(['HUMAN_REVIEW_REQUIRED', 'CANNOT_PROCEED']);
export type Route = z.infer<typeof routeSchema>;

export const roleSchema = z.enum(['REQUESTER', 'REVIEWER', 'ADMINISTRATOR']);
export type Role = z.infer<typeof roleSchema>;

export const supportStateSchema = z.enum([
  'SUPPORTED',
  'PARTIALLY_SUPPORTED',
  'UNSUPPORTED',
  'CONFLICTED',
  'NOT_APPLICABLE',
]);

export const dispositionValueSchema = z.enum([
  'RETURN_FOR_CLARIFICATION',
  'ACCEPT_AS_TEST_EVIDENCE',
  'REJECT_AS_TEST_EVIDENCE',
]);
export type DispositionValue = z.infer<typeof dispositionValueSchema>;

export const noticeSchema = z.object({
  notice_id: z.string(),
  heading_en: z.string(),
  text_en: z.string(),
  heading_ar: z.string(),
  text_ar: z.string(),
});
export type Notice = z.infer<typeof noticeSchema>;

export const demoIdentitySchema = z.object({
  identity_id: z.string(),
  display_name_en: z.string(),
  display_name_ar: z.string(),
  role: roleSchema,
  capabilities: z.array(z.string()),
  prohibitions: z.array(z.string()),
});
export type DemoIdentity = z.infer<typeof demoIdentitySchema>;

export const sessionSchema = z.object({
  token: z.string(),
  identity_id: z.string(),
  role: roleSchema,
  expires_at: z.string(),
  notices: z.array(noticeSchema),
});

export const meSchema = z.object({
  identity_id: z.string(),
  display_name_en: z.string(),
  display_name_ar: z.string(),
  role: roleSchema,
  role_id: z.string(),
  business_scope_id: z.string(),
  environment_id: z.string(),
  data_boundary_id: z.string(),
  session_expires_at: z.string(),
  capabilities: z.array(z.string()),
  prohibitions: z.array(z.string()),
  notices: z.array(noticeSchema),
  brand_statement_en: z.string(),
  brand_statement_ar: z.string(),
});
export type Me = z.infer<typeof meSchema>;

export const useCaseSchema = z.object({
  use_case_contract_id: z.string(),
  title_en: z.string(),
  title_ar: z.string(),
  description_en: z.string(),
  description_ar: z.string(),
  permitted_purpose: z.string(),
  permitted_question_kinds: z.array(z.string()),
  excluded_scope_terms: z.array(z.string()),
  excluded_outcomes: z.array(z.string()),
  max_question_chars: z.number(),
  min_question_chars: z.number(),
  business_scope_id: z.string(),
  data_boundary_id: z.string(),
});
export type UseCase = z.infer<typeof useCaseSchema>;

export const caseSummarySchema = z.object({
  case_id: z.string(),
  requester_identity_id: z.string(),
  normalised_question: z.string(),
  current_state: z.string(),
  stage: z.number().nullable(),
  route: z.string().nullable(),
  reason_code: z.string().nullable(),
  reason_message: z.string().nullable(),
  submitted_at: z.string(),
  updated_at: z.string(),
  packet_available: z.boolean(),
  permissible_next_actions: z.array(z.string()),
});
export type CaseSummary = z.infer<typeof caseSummarySchema>;

export const caseListSchema = z.object({ cases: z.array(caseSummarySchema) });

export const transitionSchema = z.object({
  sequence: z.number(),
  from_state: z.string().nullable(),
  to_state: z.string(),
  reason_code: z.string().nullable(),
  reason_message: z.string().nullable(),
  actor_id: z.string(),
  occurred_at: z.string(),
});

export const ruleResultSchema = z.object({
  rule_id: z.string(),
  rule_version: z.string(),
  outcome: z.string(),
  reason_code: z.string(),
  effect: z.string(),
  precedence_rank: z.number(),
  detail: z.string(),
  evaluated_at: z.string(),
});
export type RuleResult = z.infer<typeof ruleResultSchema>;

export const limitSchema = z.object({
  key: z.string(),
  hard_limit: z.number(),
  unit: z.string(),
  failure_reason_code: z.string(),
});

export const progressSchema = z.object({
  case: caseSummarySchema,
  transitions: z.array(transitionSchema),
  rule_results: z.array(ruleResultSchema),
  limits: z.array(limitSchema),
  stop_record: z.record(z.unknown()).nullable(),
});
export type Progress = z.infer<typeof progressSchema>;

export const evidenceLinkSchema = z.object({
  excerpt_id: z.string(),
  source_id: z.string(),
  source_version: z.string(),
  page_number: z.number(),
  section_heading: z.string(),
  char_start: z.number(),
  char_end: z.number(),
  quoted_text: z.string(),
  quote_verified: z.boolean(),
});

export const claimSchema = z.object({
  claim_id: z.string(),
  claim_ref: z.string(),
  statement: z.string(),
  materiality: z.enum(['MATERIAL', 'NON_MATERIAL']),
  support_state: supportStateSchema,
  evidence_links: z.array(evidenceLinkSchema),
  conflict_ids: z.array(z.string()),
  qualification: z.string(),
  verification_note: z.string(),
});
export type Claim = z.infer<typeof claimSchema>;

export const packetSchema = z.object({
  identity: z.object({
    packet_id: z.string(),
    packet_version: z.number(),
    case_id: z.string(),
    environment_id: z.string(),
    business_scope_id: z.string(),
    data_boundary_id: z.string(),
    created_at: z.string(),
  }),
  authorization_context: z.object({
    authorization_id: z.string(),
    fixture_notice: z.string(),
    use_case_contract_id: z.string(),
    authorization_status: z.string(),
    source_manifest_sha256: z.string(),
  }),
  request_context: z.object({
    requester_identity_id: z.string(),
    requester_role: z.string(),
    submitted_at: z.string(),
    normalised_question: z.string(),
    permitted_purpose: z.string(),
    question_sha256: z.string(),
  }),
  evidence_manifest: z.array(
    z.object({
      excerpt_id: z.string(),
      source_id: z.string(),
      source_version: z.string(),
      authority_class: z.string(),
      page_number: z.number(),
      section_heading: z.string(),
      char_start: z.number(),
      char_end: z.number(),
      excerpt_sha256: z.string(),
      retrieved_at: z.string(),
      trust_label: z.string(),
    }),
  ),
  claim_ledger: z.array(claimSchema),
  rule_results: z.array(ruleResultSchema.partial({ detail: true })),
  uncertainty: z.array(
    z.object({
      uncertainty_id: z.string(),
      kind: z.string(),
      description_en: z.string(),
      description_ar: z.string(),
      affected_source_ids: z.array(z.string()),
      increases_risk: z.boolean(),
    }),
  ),
  conflicts: z.array(z.string()),
  risk: z.object({
    factors: z.array(
      z.object({
        factor_id: z.string(),
        label_en: z.string(),
        label_ar: z.string(),
        level: z.string(),
        rationale: z.string(),
      }),
    ),
    dominant_factor_id: z.string(),
    inherent_risk: z.string(),
    reviewer_seniority_required: z.string(),
    review_depth_required: z.string(),
    method: z.string(),
  }),
  limitations: z.array(z.string()),
  route: routeSchema,
  route_reason_code: z.string(),
  version_lineage: z.record(z.string()),
  integrity: z.object({
    canonical_json_profile: z.string(),
    hash_algorithm: z.string(),
    verifier_method: z.string(),
    calculated_at: z.string(),
    packet_sha256: z.string(),
    tamper_evidence_note: z.string(),
  }),
  audit_binding: z.object({
    pre_issuance_event_id: z.string().nullable(),
    disposition_closure_event_id: z.string().nullable(),
    audit_chain_head_hash: z.string().nullable(),
  }),
  notices: z.array(noticeSchema.extend({ template_version: z.string() })),
  prototype_status: z.object({
    built: z.string(),
    integration: z.string(),
    operational: z.string(),
    authorization: z.string(),
  }),
  disposition: z
    .object({
      disposition_id: z.string(),
      disposition_value: dispositionValueSchema,
      human_rationale: z.string(),
      reviewer_identity_id: z.string(),
      decided_at: z.string(),
      is_final: z.boolean(),
      non_execution_notice: z.string(),
    })
    .nullable(),
});
export type Packet = z.infer<typeof packetSchema>;

export const packetResponseSchema = z.object({
  packet: packetSchema,
  canonical_sha256: z.string(),
  seal_verified: z.boolean(),
});

export const excerptSchema = z.object({
  excerpt_id: z.string(),
  case_id: z.string(),
  source_id: z.string(),
  source_version: z.string(),
  source_title: z.string(),
  authority_class: z.string(),
  lifecycle: z.string(),
  page_number: z.number(),
  section_heading: z.string(),
  char_start: z.number(),
  char_end: z.number(),
  text: z.string(),
  text_sha256: z.string(),
  source_sha256: z.string(),
  trust_label: z.string(),
  citation_label: z.string(),
  revocation_warning: z.string().nullable(),
});
export type Excerpt = z.infer<typeof excerptSchema>;

export const sourcePageSchema = z.object({
  source_id: z.string(),
  source_version: z.string(),
  title: z.string(),
  lifecycle: z.string(),
  page_number: z.number(),
  page_count: z.number(),
  section_headings: z.array(z.string()),
  char_start: z.number(),
  char_end: z.number(),
  text: z.string(),
  trust_label: z.string(),
  revocation_warning: z.string().nullable(),
});

export const auditEventSchema = z.object({
  event_id: z.string(),
  sequence: z.number(),
  event_type: z.string(),
  application_time: z.string(),
  actor_id: z.string(),
  actor_kind: z.string(),
  outcome: z.string(),
  reason_code: z.string().nullable(),
  severity: z.string().nullable(),
  from_state: z.string().nullable(),
  to_state: z.string().nullable(),
  object_kind: z.string().nullable(),
  object_id: z.string().nullable(),
  previous_event_hash: z.string(),
  event_hash: z.string(),
  confirmed: z.boolean(),
});

export const auditResponseSchema = z.object({
  case_id: z.string(),
  events: z.array(auditEventSchema),
  verification: z.object({
    verified: z.boolean(),
    event_count: z.number(),
    chain_version: z.string(),
    head_hash: z.string().nullable(),
    first_divergence_sequence: z.number().nullable(),
    first_divergence_kind: z.string().nullable(),
    checked_at: z.string(),
  }),
});

export const lineageSchema = z.object({
  case_id: z.string(),
  nodes: z.array(
    z.object({
      node_id: z.string(),
      kind: z.string(),
      label: z.string(),
      detail: z.string(),
    }),
  ),
  edges: z.array(z.object({ source: z.string(), target: z.string(), relation: z.string() })),
});
export type Lineage = z.infer<typeof lineageSchema>;

export const dispositionResponseSchema = z.object({
  case_id: z.string(),
  disposition_id: z.string(),
  disposition_value: dispositionValueSchema,
  is_final: z.boolean(),
  terminal_state: z.string(),
  closure_event_id: z.string(),
  packet_sha256: z.string(),
  non_execution_notice: z.string(),
});

export const killSwitchSchema = z.object({
  active: z.boolean(),
  changed_at: z.string().nullable(),
  changed_by: z.string().nullable(),
  reason: z.string().nullable(),
});

export const configurationSchema = z.object({
  environment_id: z.string(),
  component_versions: z.record(z.string()),
  corpus_manifest_sha256: z.string(),
  rule_catalog: z.array(
    z.object({
      rule_id: z.string(),
      rule_version: z.string(),
      catalog_version: z.string(),
      precedence_rank: z.number(),
      purpose: z.string(),
      evaluated_in_states: z.array(z.string()),
    }),
  ),
  limits: z.array(limitSchema),
  state_machine: z.array(
    z.object({
      stage: z.number().nullable(),
      state: z.string(),
      permitted_next_states: z.array(z.string()),
      failure_reason_code: z.string().nullable(),
      terminal: z.boolean(),
    }),
  ),
  model_configurations: z.array(z.record(z.unknown())),
  settings: z.record(z.unknown()),
  prohibited_integrations: z.array(
    z.object({
      integration_id: z.string(),
      category: z.string(),
      enforcement: z.string(),
      status: z.string(),
    }),
  ),
  kill_switch: killSwitchSchema,
  status: z.object({
    built: z.string(),
    integration: z.string(),
    operational: z.string(),
    authorization: z.string(),
  }),
});
export type Configuration = z.infer<typeof configurationSchema>;

export const tevvRunSchema = z.object({
  tevv_run_id: z.string(),
  plan_version: z.string(),
  executor: z.string(),
  started_at: z.string(),
  completed_at: z.string().nullable(),
  component_versions: z.record(z.string()),
  summary: z.record(z.unknown()),
  results: z.array(
    z.object({
      scenario_id: z.string(),
      title: z.string(),
      category: z.string(),
      repetition: z.number(),
      status: z.string(),
      expected: z.record(z.unknown()),
      actual: z.record(z.unknown()),
      case_id: z.string().nullable(),
      trace_id: z.string(),
      defect_ids: z.array(z.string()),
      executed_at: z.string(),
    }),
  ),
});
export type TevvRun = z.infer<typeof tevvRunSchema>;

export const errorEnvelopeSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    case_id: z.string().nullable(),
    state: z.string().nullable(),
    correlation_id: z.string(),
    safe_to_display: z.boolean(),
  }),
});
