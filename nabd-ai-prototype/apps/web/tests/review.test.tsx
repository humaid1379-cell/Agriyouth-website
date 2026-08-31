import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { PacketPage } from '../src/routes/PacketPage';
import { ReviewCasePage } from '../src/routes/ReviewCasePage';
import { SessionProvider } from '../src/features/session/SessionContext';
import { CasesPage } from '../src/routes/CasesPage';
import { mockApi, renderWithProviders } from './helpers';

const NOTICES = [
  {
    notice_id: 'NOTICE_DECISION_SUPPORT_ONLY',
    template_version: 'packet-notices-v1.0.0',
    heading_en: 'Decision-support only',
    text_en:
      'NABD AI has prepared a cited Decision Readiness Packet. It has not approved, executed, transmitted, or activated any institutional action.',
    heading_ar: 'لدعم القرار فقط',
    text_ar: 'نص',
  },
  {
    notice_id: 'NOTICE_HUMAN_AUTHORITY',
    template_version: 'packet-notices-v1.0.0',
    heading_en: 'Human authority',
    text_en:
      'An authorized human retains final authority and must act separately under the applicable institutional procedure.',
    heading_ar: 'السلطة البشرية',
    text_ar: 'نص',
  },
  {
    notice_id: 'NOTICE_EVIDENCE_LIMITATION',
    template_version: 'packet-notices-v1.0.0',
    heading_en: 'Evidence limitation',
    text_en:
      'Retrieved sources and model outputs are treated as untrusted data. Claims are limited to the admitted synthetic evidence recorded in this packet.',
    heading_ar: 'حدود الأدلة',
    text_ar: 'نص',
  },
  {
    notice_id: 'NOTICE_PROTOTYPE_SCOPE',
    template_version: 'packet-notices-v1.0.0',
    heading_en: 'Prototype scope',
    text_en:
      'This packet was generated in ISOLATED_PROTOTYPE_V1 using synthetic data only. It does not demonstrate production, operational, or institutional authorization.',
    heading_ar: 'نطاق النموذج الأولي',
    text_ar: 'نص',
  },
];

const PACKET = {
  packet: {
    identity: {
      packet_id: 'PKT-1',
      packet_version: 1,
      case_id: 'CASE-1',
      environment_id: 'ISOLATED_PROTOTYPE_V1',
      business_scope_id: 'BUSINESS_UNIT_V1',
      data_boundary_id: 'SYNTHETIC_ONLY',
      created_at: '2026-01-01T00:00:00.000Z',
    },
    authorization_context: {
      authorization_id: 'SYNTHETIC_DEMO_AUTHORIZATION',
      fixture_notice: 'TEST FIXTURE',
      use_case_contract_id: 'UC-POLICY-SOP-EVIDENCE-V1',
      authorization_status: 'NOT_GRANTED',
      source_manifest_sha256: 'a'.repeat(64),
    },
    request_context: {
      requester_identity_id: 'requester.analyst@demo.nabd.local',
      requester_role: 'REQUESTER',
      submitted_at: '2026-01-01T00:00:00.000Z',
      normalised_question: 'What evidence must accompany an exception request?',
      permitted_purpose: 'INTERNAL_POLICY_SOP_EVIDENCE_LOOKUP',
      question_sha256: 'b'.repeat(64),
    },
    evidence_manifest: [
      {
        excerpt_id: 'EXC-1',
        source_id: 'POL-001',
        source_version: 'v1',
        authority_class: 'GOVERNING_POLICY',
        page_number: 2,
        section_heading: '3. Evidence Requirements',
        char_start: 100,
        char_end: 200,
        excerpt_sha256: 'c'.repeat(64),
        retrieved_at: '2026-01-01T00:00:00.000Z',
        trust_label: 'UNTRUSTED_CONTENT',
      },
    ],
    claim_ledger: [
      {
        claim_id: 'CLM-1',
        claim_ref: 'C01',
        statement: 'Three mandatory evidence items are required.',
        materiality: 'MATERIAL',
        support_state: 'SUPPORTED',
        evidence_links: [
          {
            excerpt_id: 'EXC-1',
            source_id: 'POL-001',
            source_version: 'v1',
            page_number: 2,
            section_heading: '3. Evidence Requirements',
            char_start: 100,
            char_end: 200,
            quoted_text: 'Three mandatory evidence items are required.',
            quote_verified: true,
          },
        ],
        conflict_ids: [],
        qualification: '',
        verification_note: '',
      },
    ],
    rule_results: [
      {
        rule_id: 'CLM-001',
        rule_version: '1.0.0',
        outcome: 'PASS',
        reason_code: 'OK',
        effect: 'CONTINUE',
        precedence_rank: 9,
        evaluated_at: '2026-01-01T00:00:00.000Z',
      },
    ],
    uncertainty: [],
    conflicts: [],
    risk: {
      factors: [
        {
          factor_id: 'RF-EVIDENCE',
          label_en: 'Evidence sufficiency',
          label_ar: 'كفاية الأدلة',
          level: 'LOW',
          rationale: 'One material claim carries an exact citation.',
        },
      ],
      dominant_factor_id: 'RF-EVIDENCE',
      inherent_risk: 'LOW',
      reviewer_seniority_required: 'Manager grade or above',
      review_depth_required: 'Standard citation and rule-result review',
      method: 'dominant-factor-v1',
    },
    limitations: ['Claims are limited to the admitted synthetic excerpts.'],
    route: 'HUMAN_REVIEW_REQUIRED',
    route_reason_code: 'HUMAN_REVIEW_REQUIRED_BY_DESIGN',
    version_lineage: { workflow_version: 'workflow-v1.0.0' },
    integrity: {
      canonical_json_profile: 'nabd-canonical-json-v1',
      hash_algorithm: 'SHA-256',
      verifier_method: 'recompute-canonical-json-sha256',
      calculated_at: '2026-01-01T00:00:00.000Z',
      packet_sha256: 'd'.repeat(64),
      tamper_evidence_note: 'This SHA-256 is a tamper-evidence reference.',
    },
    audit_binding: {
      pre_issuance_event_id: 'EVT-1',
      disposition_closure_event_id: null,
      audit_chain_head_hash: 'e'.repeat(64),
    },
    notices: NOTICES,
    prototype_status: {
      built: 'NOT_EVIDENCED',
      integration: 'NOT_EVIDENCED',
      operational: 'NOT_EVIDENCED',
      authorization: 'NOT_GRANTED',
    },
    disposition: null,
  },
  canonical_sha256: 'd'.repeat(64),
  seal_verified: true,
};

const ME_REVIEWER = {
  identity_id: 'reviewer.manager@demo.nabd.local',
  display_name_en: 'Synthetic independent reviewer (manager)',
  display_name_ar: 'المراجع',
  role: 'REVIEWER',
  role_id: 'ROLE_SYNTHETIC_REVIEWER_V1',
  business_scope_id: 'BUSINESS_UNIT_V1',
  environment_id: 'ISOLATED_PROTOTYPE_V1',
  data_boundary_id: 'SYNTHETIC_ONLY',
  session_expires_at: '2030-01-01T00:00:00.000Z',
  capabilities: [],
  prohibitions: [],
  notices: NOTICES,
  brand_statement_en: 'Governed intelligence. Human authority.',
  brand_statement_ar: 'ذكاء محكوم. سلطة بشرية.',
};

function renderReview() {
  window.sessionStorage.setItem('nabd.demo.session', 'token');
  mockApi({ '/api/v1/me': ME_REVIEWER, '/packet': PACKET });
  return renderWithProviders(
    <SessionProvider>
      <Routes>
        <Route path="/review/:caseId" element={<ReviewCasePage />} />
      </Routes>
    </SessionProvider>,
    { route: '/review/CASE-1' },
  );
}

describe('reviewer disposition form', () => {
  it('offers only the three test-only outcomes and no approve action', async () => {
    renderReview();
    await screen.findByRole('heading', { name: /test-only disposition/i });

    expect(screen.getByRole('radio', { name: /return for clarification/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /accept as test evidence/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /reject as test evidence/i })).toBeInTheDocument();
    expect(screen.getAllByRole('radio')).toHaveLength(3);

    expect(screen.queryByRole('button', { name: /^approve$/i })).toBeNull();
    expect(screen.queryByRole('radio', { name: /^approve/i })).toBeNull();
    const body = document.body.textContent?.toLowerCase() ?? '';
    expect(body).not.toContain('approve the');
    expect(body).not.toContain('production ready');
  });

  it('keeps submit disabled until the rationale reaches the minimum length', async () => {
    const user = userEvent.setup();
    renderReview();
    const submit = await screen.findByRole('button', { name: /record test-only disposition/i });
    expect(submit).toBeDisabled();

    const rationale = screen.getByLabelText(/your rationale/i);
    await user.type(rationale, 'too short');
    expect(submit).toBeDisabled();
    expect(screen.getByText(/a substantive rationale is required/i)).toBeInTheDocument();

    await user.clear(rationale);
    await user.type(rationale, 'Checked every cited passage against the claim ledger.');
    await waitFor(() => expect(submit).toBeEnabled());
  });

  it('states that no disposition approves, executes, transmits or activates anything', async () => {
    renderReview();
    expect(
      await screen.findByText(
        /none of them approves, executes, transmits or activates any institutional action/i,
      ),
    ).toBeInTheDocument();
  });
});

describe('packet view', () => {
  it('renders all four fixed notices verbatim', async () => {
    window.sessionStorage.setItem('nabd.demo.session', 'token');
    mockApi({ '/api/v1/me': ME_REVIEWER, '/packet': PACKET });
    renderWithProviders(
      <SessionProvider>
        <Routes>
          <Route path="/cases/:caseId/packet" element={<PacketPage />} />
        </Routes>
      </SessionProvider>,
      { route: '/cases/CASE-1/packet' },
    );

    expect(await screen.findByText('Decision-support only')).toBeInTheDocument();
    expect(screen.getByText('Human authority')).toBeInTheDocument();
    expect(screen.getByText('Evidence limitation')).toBeInTheDocument();
    expect(screen.getByText('Prototype scope')).toBeInTheDocument();
    expect(
      screen.getByText(
        /has not approved, executed, transmitted, or activated any institutional action/i,
      ),
    ).toBeInTheDocument();
  });

  it('shows the four status dimensions separately and never merged', async () => {
    window.sessionStorage.setItem('nabd.demo.session', 'token');
    mockApi({ '/api/v1/me': ME_REVIEWER, '/packet': PACKET });
    renderWithProviders(
      <SessionProvider>
        <Routes>
          <Route path="/cases/:caseId/packet" element={<PacketPage />} />
        </Routes>
      </SessionProvider>,
      { route: '/cases/CASE-1/packet' },
    );

    await screen.findByText('Prototype status');
    expect(screen.getAllByText('NOT_EVIDENCED')).toHaveLength(3);
    expect(screen.getByText('NOT_GRANTED')).toBeInTheDocument();
    const body = document.body.textContent ?? '';
    expect(body).not.toMatch(/\bready\b/i);
  });
});

describe('case list', () => {
  it('renders no green readiness indicator', async () => {
    window.sessionStorage.setItem('nabd.demo.session', 'token');
    mockApi({
      '/api/v1/me': ME_REVIEWER,
      '/api/v1/cases': {
        cases: [
          {
            case_id: 'CASE-1',
            requester_identity_id: 'requester.analyst@demo.nabd.local',
            normalised_question: 'What evidence is required?',
            current_state: 'AWAITING_AUTHORIZED_HUMAN_REVIEW',
            stage: 15,
            route: 'HUMAN_REVIEW_REQUIRED',
            reason_code: null,
            reason_message: null,
            submitted_at: '2026-01-01T00:00:00.000Z',
            updated_at: '2026-01-01T00:00:00.000Z',
            packet_available: true,
            permissible_next_actions: ['VIEW_PACKET'],
          },
        ],
      },
    });
    const { container } = renderWithProviders(
      <SessionProvider>
        <CasesPage />
      </SessionProvider>,
    );

    await screen.findByText('Human review required');
    expect(container.innerHTML).not.toContain('#2E8168');
    expect(document.body.textContent?.toLowerCase()).not.toContain('approved');
  });
});

describe('no external egress', () => {
  it('makes no request to a host outside the API origin', async () => {
    renderReview();
    await screen.findByRole('heading', { name: /test-only disposition/i });

    const calls = (globalThis.fetch as unknown as { mock: { calls: unknown[][] } }).mock.calls;
    for (const [input] of calls) {
      const url = String(input);
      expect(url.startsWith('/api/') || url.startsWith('/health')).toBe(true);
    }
    expect(vi.isMockFunction(globalThis.fetch)).toBe(true);
  });
});
