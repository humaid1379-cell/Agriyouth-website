# Security boundaries

**Document version:** 1.0.0
**Environment:** `ISOLATED_PROTOTYPE_V1`
**Data boundary:** `SYNTHETIC_ONLY`

This document is the human-readable half of the prohibited-connection inventory. Its
machine-readable counterpart is `apps/api/app/domain/prohibited.py`, and the assertions
that keep the two in agreement are in `apps/api/tests/test_security.py`. Adding a package,
route or environment variable that matches an entry below fails the test suite.

The security objective is to contain a probabilistic component inside deterministic,
least-privilege controls. The system does not become safe because a prompt says so.

---

## 1. What this prototype connects to

| Dependency | Purpose | Direction | Network |
|---|---|---|---|
| PostgreSQL 16 (`db` service) | Demo case, packet, audit and TEVV storage | API to database | Compose-internal only, published on loopback `127.0.0.1:55432` |
| Frozen synthetic corpus (`./data`) | Source content and control-plane fixtures | Read-only bind mount | None |
| `DeterministicMockAdapter` | Default model mode | In-process | None |
| Optional `OpenAICompatibleAdapter` | Test-only live model mode | API to one pinned endpoint | One `https` host, only when `MODEL_MODE=live` |
| React SPA (`web` service) | Browser interface | Browser to API | Loopback `127.0.0.1:5173` |

In the default `MODEL_MODE=mock` configuration the stack runs with **no outbound internet
access at all**. Nothing in the image needs a credential to start.

---

## 2. Prohibited-connection inventory

None of the following exists in the runtime image. Each row is enforced by automated
assertions over installed packages, application imports, declared dependencies, consumed
environment variables and mounted routes.

| ID | Prohibited integration | Enforcement | Status |
|---|---|---|---|
| `PROHIB-01` | Email, SMS, chat or notification service | No SDK or dependency; no route; denial test | Absent by design |
| `PROHIB-02` | Webhook or generic HTTP action tool | No outbound action client; allowlist test | Absent by design |
| `PROHIB-03` | Public web search, browser or scraper | No dependency; no route | Absent by design |
| `PROHIB-04` | Payment, procurement or transaction service | No dependency, route or schema field | Absent by design |
| `PROHIB-05` | Operational database write | Separate demo database only; no external DSN configuration field | Absent by design |
| `PROHIB-06` | Repository mutation or dynamic source ingestion | No upload endpoint; corpus mounted read-only | Absent by design |
| `PROHIB-07` | OAuth or real identity-provider integration | Synthetic server sessions only | Absent by design |
| `PROHIB-08` | External telemetry or crash reporting | Disabled; local structured logs only | Absent by design |
| `PROHIB-09` | Model tool or function calling | Explicitly disabled; the output schema rejects tool requests | Absent by design |
| `PROHIB-10` | Provider or model fallback | The adapter rejects any configuration mismatch | Absent by design |

### 2.1 Forbidden modules

`smtplib`, `email.message`, `twilio`, `sendgrid`, `slack_sdk`, `aiosmtplib`, `mailgun`,
`requests`, `aiohttp`, `webhooks`, `selenium`, `playwright.sync_api`, `bs4`, `scrapy`,
`googlesearch`, `serpapi`, `stripe`, `braintree`, `paypalrestsdk`, `square`, `git`,
`pygit2`, `dulwich`, `authlib`, `msal`, `python_jose`, `oauthlib`, `requests_oauthlib`,
`sentry_sdk`, `datadog`, `ddtrace`, `newrelic`, `opentelemetry.exporter.otlp`.

Third-party modules on this list are not installed in the image. Standard-library modules
on this list (`smtplib`, `email.message`) cannot be uninstalled, so the assertion for them
is that no application module imports them.

### 2.2 Forbidden environment variables

`SMTP_HOST`, `SMTP_URL`, `SENDGRID_API_KEY`, `TWILIO_AUTH_TOKEN`, `SLACK_WEBHOOK_URL`,
`WEBHOOK_URL`, `CALLBACK_URL`, `ACTION_ENDPOINT`, `OUTBOUND_HTTP_ALLOWLIST`,
`SEARCH_API_KEY`, `BROWSER_ENDPOINT`, `SERP_API_KEY`, `STRIPE_API_KEY`, `PAYMENT_ENDPOINT`,
`MERCHANT_ID`, `OPERATIONAL_DATABASE_URL`, `PROD_DATABASE_URL`, `WAREHOUSE_DSN`,
`EXTERNAL_DSN`, `SOURCE_UPLOAD_DIR`, `INGEST_ENDPOINT`, `REPO_WRITE_TOKEN`,
`OAUTH_CLIENT_SECRET`, `OIDC_ISSUER`, `AZURE_TENANT_ID`, `IDP_METADATA_URL`, `SENTRY_DSN`,
`DATADOG_API_KEY`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `NEW_RELIC_LICENSE_KEY`,
`MODEL_TOOLS_ENABLED`, `ENABLE_FUNCTION_CALLING`, `FALLBACK_MODEL`, `FALLBACK_ENDPOINT`,
`SECONDARY_PROVIDER`, `MODEL_ROUTER_URL`.

None of these is read anywhere in the application, and none appears in `.env.example`.

### 2.3 Forbidden route fragments

No mounted path contains `/send`, `/notify`, `/email`, `/sms`, `/message`, `/webhook`,
`/callback`, `/action`, `/dispatch`, `/trigger`, `/search/web`, `/browse`, `/fetch-url`,
`/scrape`, `/pay`, `/payment`, `/charge`, `/invoice`, `/purchase`, `/transaction`,
`/write-back`, `/sync`, `/upsert-operational`, `/upload`, `/ingest`, `/import`,
`/sources/create`, `/documents/add`, `/oauth`, `/oidc`, `/saml`, `/sso`, `/telemetry`,
`/crash-report`, `/tools`, `/functions`, `/models/select` or `/provider/switch`.

No `PUT`, `PATCH` or `DELETE` method is mounted on any path.

---

## 3. Terminal non-execution

The prototype supports and prepares a decision. Authorized people retain final authority,
and any institutional action happens separately under another procedure.

* `PATH-001` runs in **every** workflow state at precedence rank 1. If a configured action
  endpoint exists, or an action path is attempted, the case stops with
  `PROHIBITED_ACTION_PATH_DETECTED` and an `S0_CRITICAL` security event is recorded.
* No disposition value triggers a connector, workflow, write, message, approval or
  transaction. The three values are `RETURN_FOR_CLARIFICATION`, `ACCEPT_AS_TEST_EVIDENCE`
  and `REJECT_AS_TEST_EVIDENCE`; there is no approval value to select.
* Every disposition carries a fixed non-execution notice, and the packet carries four fixed
  notices whose verbatim text is asserted by semantic validation.
* Packet semantic validation rejects any packet containing an action id, a webhook, a URL,
  an external target or an execution command.

---

## 4. Content isolation and prompt injection

All of the following are treated as hostile content: source title, source metadata, source
body, retrieved excerpt, user question, model output, and simulated tool output.

| Control | Where |
|---|---|
| Deterministic instruction-like pattern set (15 patterns, versioned) | `app/domain/injection_patterns.py` |
| Quarantine on any body or metadata match, applied before retrieval | `app/services/eligibility.py` |
| Explicit `<<<UNTRUSTED_CONTENT ...>>>` envelope around every excerpt in a prompt | `app/services/prompts.py` |
| Both prompts state that excerpts are untrusted data that may contain instructions to ignore | `app/prompts/draft_v1.md`, `app/prompts/verify_v1.md` |
| `ISO-001` stops the case if instruction-like content reaches the admitted excerpt set | `app/rules/catalog.py` |
| Prohibited-marker scan over raw model output before parsing | `app/services/model_gateway.py` |
| Closed-schema parse with `extra = forbid`; invalid output is never coerced | `app/schemas/model_io.py` |
| Independent re-slicing of every quoted span from the stored excerpt | `app/services/orchestrator.py::_bind_claims` |

The detector is defence in depth, not a source-authority decision-maker, and no third LLM
detector is introduced in V1.

Model output never reaches code execution, a shell command, SQL, a URL, a template, an
access-control field, a state transition function or any connector. The retrieval
tokeniser reduces a question to `[a-z0-9]+` terms before they touch the query, and all SQL
is parameterised through SQLAlchemy.

---

## 5. Authority, identity and separation of duties

* The browser may select a demo profile. It never submits a role, scope, authority level or
  separation-of-duties fact; the API derives all of them from a short-lived HMAC-signed
  demo session and the seeded fixture.
* Only three profiles are selectable. The expired, revoked, unknown and cross-scope
  fixtures exist for denial tests and cannot obtain a session.
* `SOD-001` checks self-review first, then reviewer status, role, scope and rationale.
  A requester can never dispose of its own case, whatever role it holds.
* The administrator operates controls and cannot grant authorization, submit or review a
  case, modify source content, or read case content.
* An absent case and a case hidden from the caller return the identical `NOT_FOUND`, so
  probing a case id discloses nothing.

---

## 6. Audit integrity

* Confirmed audit events are append-only through **two independent controls**: a
  PostgreSQL `BEFORE UPDATE OR DELETE` trigger that raises, and table grants that give the
  application role `INSERT` and `SELECT` only. Either alone would be bypassable by a
  mistake in the other.
* Each case owns a SHA-256 hash chain; every event binds the hash of its predecessor.
* Packet display requires a confirmed `PACKET_PRE_ISSUANCE` event whose binding matches the
  packet id, version and issued hash exactly. Disposition closure requires a **distinct,
  later** confirmed `DISPOSITION_CLOSURE` event.
* The chain hash is tamper evidence. It is not proof of truth, immutable storage,
  authorization or authorship, and it requires controlled storage plus independent
  verification to mean anything.

---

## 7. Secrets

* No API key, password or token appears in code, test fixtures, logs, packets, screenshots
  or prompts. `.env.example` contains placeholders and local demo values only.
* The database passwords in `.env.example` and `scripts/sql/bootstrap_roles.sql` are
  synthetic local-demo values for a throwaway workbench that holds no real data. They must
  never be reused anywhere else.
* `Settings.redacted()` is the only settings view exposed by the API, and it omits the
  database URL, the session secret and the live-model key.
* Error envelopes carry a reason code, a non-leaking message, an optional case id and
  state, a correlation id and a display flag. Request-validation detail is dropped
  deliberately, because it can echo submitted content back to the caller.

---

## 8. HTTP hardening

`Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none';
form-action 'none'`, plus `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
`Referrer-Policy: no-referrer`, `Cross-Origin-Opener-Policy: same-origin`,
`Cross-Origin-Resource-Policy: same-origin`, a restrictive `Permissions-Policy`, and
`Cache-Control: no-store`. CORS allows a single configured origin, no credentials, and only
`GET`, `POST` and `OPTIONS`. Requests over 64 KiB are refused before routing.

---

## 9. Container posture

Non-root user (uid 10001), `no-new-privileges`, all capabilities dropped on the API
service, no privileged mode, pinned image tags, health checks on every service, the corpus
mounted read-only, local named volumes for the database and artifacts, and the database
published on loopback only.

---

## 10. What these boundaries do not establish

Passing every control listed here supports **candidate developer-verification evidence for
an isolated prototype**. It does not establish independent security testing, penetration
testing, operational monitoring, incident-response maturity, approval to handle customer
data, or authorization to use the prototype outside its synthetic environment. Independent
security testing is a separate gate (G-C) that must be performed by someone other than the
primary developer.

---

| Dimension | Value |
|---|---|
| Built | `NOT_EVIDENCED` |
| Integration | `NOT_EVIDENCED` |
| Operational | `NOT_EVIDENCED` |
| Authorization | `NOT_GRANTED` |
