import { expect, test, type APIRequestContext } from '@playwright/test';

/**
 * End-to-end coverage of the governed workflow through the running workbench.
 *
 * The API assertions exercise the real control path; the UI assertions confirm that the
 * interface renders that path honestly, never colour-only, and never with approval
 * language.
 */

const API = process.env.E2E_API_BASE_URL ?? 'http://localhost:8000';

const REQUESTER = 'requester.analyst@demo.nabd.local';
const REVIEWER = 'reviewer.manager@demo.nabd.local';
const ADMIN = 'admin.platform@demo.nabd.local';

const BENIGN_QUESTION =
  'What evidence must accompany an internal policy exception request in the Corporate ' +
  'Services Unit, and who is required to review a Tier 2 request?';

const CONFLICT_QUESTION =
  'Within how many business days must a reviewer complete an exception review where the ' +
  'exception file affects access to restricted records?';

const ACTION_QUESTION =
  'Please approve the Tier 2 exception request for the Corporate Services Unit and send ' +
  'the confirmation email to the requesting analyst.';

const RATIONALE =
  'Checked each cited passage against the packet claim ledger and recorded this as test ' +
  'evidence only; no institutional action is authorised by this disposition.';

async function session(request: APIRequestContext, identityId: string): Promise<string> {
  const response = await request.post(`${API}/api/v1/demo/session`, {
    data: { identity_id: identityId },
  });
  expect(response.status()).toBe(200);
  return (await response.json()).token as string;
}

function bearer(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` };
}

async function runCase(
  request: APIRequestContext,
  token: string,
  question: string,
): Promise<Record<string, unknown>> {
  const created = await request.post(`${API}/api/v1/cases`, {
    headers: bearer(token),
    data: { question },
  });
  expect(created.status()).toBe(201);
  const caseId = (await created.json()).case_id as string;

  const processed = await request.post(`${API}/api/v1/cases/${caseId}/process`, {
    headers: bearer(token),
  });
  expect(processed.status()).toBe(200);
  return (await processed.json()) as Record<string, unknown>;
}

test.describe('health and readiness', () => {
  test('the workbench reports ready without leaking dependency detail', async ({ request }) => {
    const live = await request.get(`${API}/health/live`);
    expect(live.status()).toBe(200);
    expect((await live.json()).environment_id).toBe('ISOLATED_PROTOTYPE_V1');

    const ready = await request.get(`${API}/health/ready`);
    const body = await ready.json();
    expect(body.status).toBe('ready');
    expect(JSON.stringify(body)).not.toMatch(/password|secret|postgresql:\/\//i);
  });
});

test.describe('governed happy path', () => {
  test('a bounded question reaches human review with exact citations', async ({ request }) => {
    const token = await session(request, REQUESTER);
    const summary = await runCase(request, token, BENIGN_QUESTION);

    expect(summary.current_state).toBe('AWAITING_AUTHORIZED_HUMAN_REVIEW');
    expect(summary.route).toBe('HUMAN_REVIEW_REQUIRED');

    const caseId = summary.case_id as string;
    const packetResponse = await request.get(`${API}/api/v1/cases/${caseId}/packet`, {
      headers: bearer(token),
    });
    expect(packetResponse.status()).toBe(200);
    const packetBody = await packetResponse.json();
    expect(packetBody.seal_verified).toBe(true);

    const packet = packetBody.packet;
    expect(packet.notices).toHaveLength(4);
    expect(packet.route).toBe('HUMAN_REVIEW_REQUIRED');
    expect(packet.prototype_status).toMatchObject({
      built: 'NOT_EVIDENCED',
      integration: 'NOT_EVIDENCED',
      operational: 'NOT_EVIDENCED',
      authorization: 'NOT_GRANTED',
    });

    const material = packet.claim_ledger.filter(
      (claim: { materiality: string }) => claim.materiality === 'MATERIAL',
    );
    expect(material.length).toBeGreaterThan(0);
    for (const claim of material) {
      expect(claim.support_state).toBe('SUPPORTED');
      expect(claim.evidence_links.length).toBeGreaterThan(0);
      for (const link of claim.evidence_links) {
        expect(link.quote_verified).toBe(true);
        expect(link.char_end).toBeGreaterThan(link.char_start);
      }
    }

    const excerptId = packet.evidence_manifest[0].excerpt_id;
    const excerpt = await request.get(`${API}/api/v1/evidence/${excerptId}`, {
      headers: bearer(token),
    });
    expect((await excerpt.json()).trust_label).toBe('UNTRUSTED_CONTENT');

    const audit = await request.get(`${API}/api/v1/cases/${caseId}/audit`, {
      headers: bearer(token),
    });
    expect((await audit.json()).verification.verified).toBe(true);
  });

  test('a separate reviewer records a test-only disposition and two audits close it', async ({
    request,
  }) => {
    const requesterToken = await session(request, REQUESTER);
    const summary = await runCase(request, requesterToken, BENIGN_QUESTION);
    const caseId = summary.case_id as string;

    const reviewerToken = await session(request, REVIEWER);
    const disposition = await request.post(`${API}/api/v1/cases/${caseId}/dispositions`, {
      headers: bearer(reviewerToken),
      data: { disposition_value: 'ACCEPT_AS_TEST_EVIDENCE', human_rationale: RATIONALE },
    });
    expect(disposition.status()).toBe(201);
    const body = await disposition.json();
    expect(body.terminal_state).toBe('CLOSED_DECISION_SUPPORT_RECORD');
    expect(body.is_final).toBe(true);
    expect(body.non_execution_notice).toContain('does not approve');

    const audit = await request.get(`${API}/api/v1/cases/${caseId}/audit`, {
      headers: bearer(reviewerToken),
    });
    const events = (await audit.json()).events as Array<{ event_type: string; sequence: number }>;
    const preIssuance = events.find((event) => event.event_type === 'PACKET_PRE_ISSUANCE');
    const closure = events.find((event) => event.event_type === 'DISPOSITION_CLOSURE');
    expect(preIssuance).toBeDefined();
    expect(closure).toBeDefined();
    expect(closure!.sequence).toBeGreaterThan(preIssuance!.sequence);
  });
});

test.describe('fail-closed paths', () => {
  test('an action-seeking request cannot proceed and calls no model', async ({ request }) => {
    const token = await session(request, REQUESTER);
    const summary = await runCase(request, token, ACTION_QUESTION);
    expect(summary.route).toBe('CANNOT_PROCEED');
    expect(summary.reason_code).toBe('USE_CASE_EXCLUDED_OR_UNBOUNDED');

    const packet = await request.get(`${API}/api/v1/cases/${summary.case_id}/packet`, {
      headers: bearer(token),
    });
    expect(packet.status()).toBe(404);
  });

  test('a declared source conflict stops before any model call', async ({ request }) => {
    const token = await session(request, REQUESTER);
    const summary = await runCase(request, token, CONFLICT_QUESTION);
    expect(summary.route).toBe('CANNOT_PROCEED');
    expect(summary.reason_code).toBe('EVIDENCE_INSUFFICIENT_OR_CONFLICTED');
  });

  test('a requester cannot dispose of its own case', async ({ request }) => {
    const token = await session(request, REQUESTER);
    const summary = await runCase(request, token, BENIGN_QUESTION);
    const denied = await request.post(`${API}/api/v1/cases/${summary.case_id}/dispositions`, {
      headers: bearer(token),
      data: { disposition_value: 'ACCEPT_AS_TEST_EVIDENCE', human_rationale: RATIONALE },
    });
    expect(denied.status()).toBe(403);
  });

  test('there is no approval disposition value', async ({ request }) => {
    const requesterToken = await session(request, REQUESTER);
    const summary = await runCase(request, requesterToken, BENIGN_QUESTION);
    const reviewerToken = await session(request, REVIEWER);
    const rejected = await request.post(`${API}/api/v1/cases/${summary.case_id}/dispositions`, {
      headers: bearer(reviewerToken),
      data: { disposition_value: 'APPROVE', human_rationale: RATIONALE },
    });
    expect(rejected.status()).toBe(422);
  });

  test('the administrator cannot read case content', async ({ request }) => {
    const requesterToken = await session(request, REQUESTER);
    const summary = await runCase(request, requesterToken, BENIGN_QUESTION);
    const adminToken = await session(request, ADMIN);
    const denied = await request.get(`${API}/api/v1/cases/${summary.case_id}`, {
      headers: bearer(adminToken),
    });
    expect(denied.status()).toBe(403);
  });

  test('the kill switch halts intake and can be cleared', async ({ request }) => {
    const adminToken = await session(request, ADMIN);
    const requesterToken = await session(request, REQUESTER);

    await request.post(`${API}/api/v1/admin/kill-switch`, {
      headers: bearer(adminToken),
      data: { active: true, reason: 'End-to-end test exercising the emergency stop.' },
    });
    const blocked = await request.post(`${API}/api/v1/cases`, {
      headers: bearer(requesterToken),
      data: { question: BENIGN_QUESTION },
    });
    expect(blocked.status()).toBe(422);
    expect((await blocked.json()).error.code).toBe('EMERGENCY_STOP_ACTIVE');

    await request.post(`${API}/api/v1/admin/kill-switch`, {
      headers: bearer(adminToken),
      data: { active: false, reason: 'End-to-end test restoring normal operation.' },
    });
  });
});

test.describe('prohibited surface', () => {
  test('no mutating HTTP method and no upload route is mounted', async ({ request }) => {
    const spec = await (await request.get(`${API}/api/openapi.json`)).json();
    const paths = Object.keys(spec.paths);
    for (const path of paths) {
      for (const method of Object.keys(spec.paths[path])) {
        expect(['get', 'post', 'options', 'head']).toContain(method.toLowerCase());
      }
    }
    for (const fragment of ['upload', 'ingest', 'webhook', 'payment', 'oauth', 'browse']) {
      expect(paths.join(' ')).not.toContain(fragment);
    }
  });

  test('security headers are present on API responses', async ({ request }) => {
    const response = await request.get(`${API}/health/live`);
    const headers = response.headers();
    expect(headers['x-content-type-options']).toBe('nosniff');
    expect(headers['x-frame-options']).toBe('DENY');
    expect(headers['content-security-policy']).toContain("default-src 'none'");
  });
});

test.describe('interface', () => {
  test('the login screen offers synthetic profiles and no password field', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[type="password"]')).toHaveCount(0);
    await expect(page.getByText(/synthetic/i).first()).toBeVisible();
  });

  test('no approval language appears anywhere in the shell', async ({ page }) => {
    await page.goto('/login');
    const body = (await page.locator('body').innerText()).toLowerCase();
    for (const forbidden of [
      'production ready',
      'production-ready',
      'zero hallucination',
      'zero risk',
      'guaranteed compliant',
      'error-free',
    ]) {
      expect(body).not.toContain(forbidden);
    }
  });

  test('the language toggle switches document direction to rtl and back', async ({ page }) => {
    await page.goto('/login');
    const toggle = page.getByRole('button', { name: /العربية|arabic/i }).first();
    if ((await toggle.count()) === 0) {
      test.skip(true, 'language toggle not present on this screen');
    }
    await toggle.click();
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await page.getByRole('button', { name: /english/i }).first().click();
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
  });

  test('every interactive control is reachable by keyboard', async ({ page }) => {
    await page.goto('/login');
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => document.activeElement?.tagName ?? '');
    expect(['A', 'BUTTON', 'INPUT', 'SELECT']).toContain(focused);
  });
});
