# API Contract

**Document version:** 1.0.0
**Environment:** `ISOLATED_PROTOTYPE_V1`

This document is the reference description of the HTTP surface that
`contracts/openapi.json` actually exports; it is not a design proposal, not an integration
guide for any external system, and not a statement that this API is authorised for
institutional use.

---

## 1. Scope of the surface

`contracts/openapi.json` is generated from the mounted FastAPI application. It contains
**22 paths and 23 operations**: 16 `GET` and 7 `POST`. Two operations (`/health/live`,
`/health/ready`) are unversioned; the remaining 21 sit under `/api/v1`.

The routers are:

| Router | Prefix | Module |
|---|---|---|
| Session | `/api/v1` | `apps/api/app/api/routes_session.py` |
| Cases | `/api/v1` | `apps/api/app/api/routes_cases.py` |
| Review | `/api/v1` | `apps/api/app/api/routes_review.py` |
| Admin | `/api/v1/admin` | `apps/api/app/api/routes_admin.py` |
| Health | (none) | inline in `apps/api/app/main.py::create_app` |

Section 13 of `docs/NABD_AI_CURSOR_FULL_PROTOTYPE_BUILD_SPEC.md` tabulates 20 operations.
The three additional operations are `GET /api/v1/demo/identities`,
`GET /api/v1/cases/{case_id}/progress` and `GET /api/v1/review/queue`. All three are
read-only and exist to serve UI routes required by Section 14.1; each is marked in the
inventory below. No operation outside Section 13 mutates anything.

### 1.1 Methods that are not mounted

**No `PUT`, `PATCH` or `DELETE` method is mounted anywhere in the application.** This is a
property of the exported contract, not a convention: every operation in
`contracts/openapi.json` is `get` or `post`, and the CORS middleware in
`app/main.py::create_app` declares `allow_methods=["GET", "POST", "OPTIONS"]`, so a browser
preflight for any other method is refused before it reaches a route.

### 1.2 Absent capabilities

There is **no generic CRUD API** for any of the following, and no route through which any
of them can be created, edited, replaced or removed:

| Object | Where it is defined instead | Why there is no API |
|---|---|---|
| Authorization | `data/fixtures/authorization.json`, read by `app/services/fixtures.py::primary_authorization` | Authorization is a human governance act recorded outside the system. A route that granted it would let the system widen its own permission. Asserted by `test_security.py::TestProhibitedRoutes::test_authorization_cannot_be_granted_through_the_api`. |
| Source governance (manifest, sources, conflicts, revocations) | `data/synthetic_policy_collection_v1/`, seeded by `scripts/seed_synthetic_corpus.py` | The corpus is frozen and hash-admitted. A write path would break the manifest hash the authorization fixture binds. |
| Rules | `app/rules/catalog.py` | The catalog is code with versioned rule identifiers. Runtime mutation would make determinism unverifiable. |
| Model configuration | `data/fixtures/model_configurations.json` | Pinning is the control. See `docs/model-configuration-card.md`. |
| Status acceptance | `artifacts/templates/human_owner_acceptance_record.md` | The four status dimensions are fixed at `NOT_EVIDENCED`/`NOT_GRANTED` by `app/api/routes_admin.py::read_configuration` and cannot be set by request (INV-16). |
| Production users, roles or an identity provider | `data/fixtures/identities.json` | Seven seeded synthetic profiles only. `app/domain/prohibited.py` lists identity-provider integration as a prohibited category. |

Two further absences are load-bearing:

- **No upload or ingestion route.** Asserted by
  `test_security.py::TestProhibitedRoutes::test_there_is_no_upload_or_ingestion_route`.
- **No route path matches a prohibited fragment.**
  `test_security.py::TestProhibitedRoutes::test_no_mounted_route_matches_a_prohibited_fragment`
  walks every mounted route and compares it against
  `app/domain/prohibited.py::PROHIBITED_ROUTE_FRAGMENTS`.

---

## 2. The single error envelope

Every failure the API returns — control failure, validation failure, framework 404, or
unhandled exception — is rendered into one shape by
`app/domain/errors.py::ControlError.envelope` and the four exception handlers in
`app/main.py::create_app`.

```json
{
  "error": {
    "code": "REQUEST_CONTRACT_INVALID",
    "message": "The request is not one bounded, in-contract synthetic policy or SOP question.",
    "case_id": null,
    "state": null,
    "correlation_id": "3f0c9c1a5e2b4f8fa1d7c6e4b9a20d31",
    "safe_to_display": true
  }
}
```

The schema is `app/schemas/api.py::ErrorEnvelope` wrapping `ErrorBody`, both
`extra = forbid`. The fields are:

| Field | Type | Meaning |
|---|---|---|
| `code` | `string` | Exactly one member of `app/domain/reason_codes.py::ReasonCode`. This is the governed value. |
| `message` | `string` | The fixed English text from `REASON_MESSAGES` for that code. It is display sugar, not a diagnostic. |
| `case_id` | `string \| null` | Present only when the failing operation was already scoped to a case the caller may see. |
| `state` | `string \| null` | A `CaseState` value, when the failure occurred at a known workflow state. |
| `correlation_id` | `string` | The per-request hex identifier set by `request_guard`; also returned in the `X-Correlation-Id` response header. |
| `safe_to_display` | `boolean` | Whether the message may be rendered to a human in the UI. |

### 2.1 What the envelope does not contain

The envelope carries no secret, no prompt, no credential, no hidden setting and no
unauthorized case content. Each of those is an explicit property of the implementation
rather than an emergent one:

- **No submitted content is echoed.** The `RequestValidationError` handler in `app/main.py`
  discards Pydantic's `errors()` payload entirely and substitutes a bare
  `REQUEST_CONTRACT_INVALID`, because Pydantic's detail includes the offending input value.
  Asserted by `test_api.py::TestErrorEnvelope::test_validation_errors_do_not_echo_submitted_content`.
- **No internal failure detail escapes.** `unhandled_handler` logs the traceback
  server-side and returns `INTERNAL_CONTROL_FAILURE` with the fixed message and HTTP 500.
  Asserted by `test_security.py::TestNoLeakage::test_error_envelopes_never_leak_infrastructure_detail`.
- **No message contains a prompt or a secret.** `REASON_MESSAGES` is a frozen dictionary of
  fixed strings. `test_contracts.py::TestReasonCodes::test_messages_do_not_leak_secrets_or_prompts`
  scans every message; `test_contracts.py::TestReasonCodes::test_every_code_has_a_message`
  ensures none is missing and therefore that no code can fall through to a raw exception
  string.
- **Absence and invisibility are indistinguishable.**
  `app/api/deps.py::load_visible_case` raises the identical `NotFoundError(NOT_FOUND)` for a
  case that does not exist, a case in another business scope, and a case belonging to
  another requester. Asserted by
  `test_api.py::TestAccessControl::test_unknown_case_id_is_indistinguishable_from_a_hidden_one`.
- **Settings are redacted where they are surfaced at all.** `app/config.py::Settings.redacted`
  omits `demo_session_secret` and the live-mode credential fields; asserted by
  `test_security.py::TestNoLeakage::test_settings_redaction_excludes_the_secret`.

### 2.2 HTTP status mapping

Status codes come from the `http_status` attribute of the raised `ControlError` subclass, so
the mapping is a property of the error type rather than of the route:

| Exception class | Status | Typical reason codes |
|---|---|---|
| `IdentityError` | 401 | `REQUESTER_OR_SESSION_INVALID` |
| `AuthorizationError` | 403 | `AUTHORIZATION_NOT_CURRENT_OR_IN_SCOPE` |
| `AccessDeniedError` | 403 | `ACCESS_DENIED`, `SEPARATION_OF_DUTIES_VIOLATION`, `REVIEWER_AUTHORITY_INVALID` |
| `SecurityError` | 403 | `PROHIBITED_ACTION_PATH_DETECTED` |
| `NotFoundError` | 404 | `NOT_FOUND`, `PACKET_NOT_AVAILABLE`, `SOURCE_QUARANTINED` |
| `IllegalTransitionError` | 409 | `ILLEGAL_STATE_TRANSITION` |
| `ControlError` (base), `StopError` | 422 | `REQUEST_CONTRACT_INVALID`, `EMERGENCY_STOP_ACTIVE`, `CRITICAL_AUDIT_FAILURE`, `DISPOSITION_*` |
| `LimitExceededError` | 429 | `CONCURRENCY_LIMIT_EXCEEDED`, `EXPORT_RATE_LIMIT_EXCEEDED` |
| (middleware, before routing) | 413 | `REQUEST_LIMIT_EXCEEDED` |
| `unhandled_handler` | 500 | `INTERNAL_CONTROL_FAILURE` |

The 413 case is worth naming separately: `app/main.py::create_app.request_guard` rejects any
request whose declared `Content-Length` exceeds `MAX_REQUEST_BYTES` (64 KiB) before the
router is reached, and constructs the envelope by hand so that the shape is identical.

### 2.3 Response headers

Every response carries the `SECURITY_HEADERS` set from `app/main.py` plus
`X-Correlation-Id`. Asserted by `test_api.py::TestErrorEnvelope::test_security_headers_are_present`.

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `no-referrer` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Resource-Policy` | `same-origin` |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=(), payment=(), usb=()` |
| `Cache-Control` | `no-store` |
| `X-Correlation-Id` | per-request hex identifier |

---

## 3. Authentication and roles

Authentication is a bearer token issued by `POST /api/v1/demo/session`. The token is
`session_id.nonce.hmac`, signed with `Settings.demo_session_secret`; only its SHA-256 is
persisted, in `demo_sessions.token_sha256`.

`app/api/deps.py::current_identity` requires an `Authorization: Bearer <token>` header and
resolves it through `app/services/identity.py::resolve_session`, which checks the HMAC, the
stored digest, the revocation flag, the expiry and the fixture status — and denies all five
with the same `REQUESTER_OR_SESSION_INVALID`.

Role gates are produced by `app/api/deps.py::require_role`:

| Alias | Admitted role |
|---|---|
| `CurrentIdentity` | any authenticated identity |
| `RequesterIdentity` | `REQUESTER` |
| `ReviewerIdentity` | `REVIEWER` |
| `AdminIdentity` | `ADMINISTRATOR` |

**No request may name its own role, scope or authority.** `app/schemas/api.py` request models
are closed and contain only: an identity id (`DemoSessionRequest`), a question string
(`CreateCaseRequest`), a disposition value with rationale and optional expected hash
(`DispositionRequest`), a kill-switch flag with reason (`KillSwitchRequest`), an optional case
id (`AuditVerifyRequest`) and an optional scenario id tuple (`TevvRunRequest`). Everything
else is derived server-side from the token. Asserted by
`test_api.py::TestSessionAndIdentity::test_client_cannot_submit_a_role_or_scope`.

Case visibility is applied on top of the role by `load_visible_case`, which enforces scope
match, requester ownership, and the rule that an administrator never reads case content.

---

## 4. Endpoint inventory

Reason codes listed per endpoint are those the endpoint can return in the error envelope.
`INTERNAL_CONTROL_FAILURE` (500) and `REQUEST_LIMIT_EXCEEDED` (413, body size) are possible on
every operation and are not repeated.

### 4.1 Health

#### `GET /health/live`

| | |
|---|---|
| Role | none |
| Request | none |
| Response 200 | `HealthResponse` — `{ status: "live", environment_id, checks: {} }` |
| Reason codes | none |

Deliberately reports no dependency detail, so an unauthenticated caller learns nothing about
the deployment. Asserted by `test_api.py::TestHealth::test_liveness_reports_no_dependency_detail`.

#### `GET /health/ready`

| | |
|---|---|
| Role | none |
| Request | none |
| Response 200 | `HealthResponse` — `status` is `ready` or `not_ready`; `checks` carries `database`, `corpus_manifest`, `rule_catalog` (each `ok` or `unavailable`) and `model_mode` |
| Reason codes | none |

The check values are fixed literals. No connection string, host, version or error text is
returned. Asserted by `test_api.py::TestHealth::test_readiness_reports_dependencies_without_secrets`.

### 4.2 Session and contract

#### `GET /api/v1/demo/identities` — *beyond Section 13; serves the `/login` UI route*

| | |
|---|---|
| Role | none |
| Request | none |
| Response 200 | `list[DemoIdentityOption]` — `identity_id`, `display_name_en`, `display_name_ar`, `role`, `capabilities`, `prohibitions` |
| Reason codes | none |

Returns only fixtures with `selectable_in_ui: true`, so the four denial fixtures (expired,
revoked, unknown, cross-scope) are never offered. Asserted by
`test_api.py::TestSessionAndIdentity::test_only_selectable_profiles_are_offered`.

#### `POST /api/v1/demo/session`

| | |
|---|---|
| Role | none |
| Request | `DemoSessionRequest` — `{ identity_id }` |
| Response 200 | `DemoSessionResponse` — `token`, `identity_id`, `role`, `expires_at`, `notices` (the four fixed bilingual notices from `app/domain/notices.py`) |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401) |

An unknown identity, a non-selectable identity and a non-`ACTIVE` identity are all denied
identically. Asserted by
`test_api.py::TestSessionAndIdentity::test_denial_fixtures_cannot_obtain_a_session`.

#### `GET /api/v1/me`

| | |
|---|---|
| Role | any authenticated |
| Request | none |
| Response 200 | `MeResponse` — identity, bilingual display names, `role`, `role_id`, `business_scope_id`, `environment_id`, `data_boundary_id`, `session_expires_at`, `capabilities`, `prohibitions`, `notices`, bilingual brand statement |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401) |

Every trusted field is read from the seeded fixture, never from the request. Asserted by
`test_api.py::TestSessionAndIdentity::test_identity_is_derived_server_side`.

#### `GET /api/v1/use-case`

| | |
|---|---|
| Role | none |
| Request | none |
| Response 200 | `UseCaseResponse` — contract id, bilingual title and description, `permitted_purpose`, `permitted_question_kinds`, `excluded_scope_terms`, `excluded_outcomes`, `max_question_chars`, `min_question_chars`, `business_scope_id`, `data_boundary_id` |
| Reason codes | none |

Read-only projection of `data/fixtures/use_case_contract.json`. The exclusions are published
so a requester can see the boundary before submitting. Asserted by
`test_api.py::TestUseCaseContract::test_contract_lists_exclusions`.

### 4.3 Cases

#### `POST /api/v1/cases`

| | |
|---|---|
| Role | `REQUESTER` |
| Request | `CreateCaseRequest` — `{ question }`, 1 to `QUESTION_MAX_CHARS` (2000) characters |
| Response 201 | `CaseSummary` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403), `EMERGENCY_STOP_ACTIVE` (422), `REQUEST_CONTRACT_INVALID` (422) |

Refuses immediately when the kill switch is active, before a case row exists. Normalises the
question (NFC, collapsed whitespace) through `app/services/orchestrator.py::build_case_row`,
records `question_sha256`, starts the case at `AUTHORIZATION_PREFLIGHT`, and appends a
`CASE_CREATED` audit event whose `payload_reference` carries the digest, not the question.

`CaseSummary` fields: `case_id`, `requester_identity_id`, `normalised_question`,
`current_state`, `stage`, `route`, `reason_code`, `reason_message`, `submitted_at`,
`updated_at`, `packet_available`, `permissible_next_actions`.

#### `POST /api/v1/cases/{case_id}/process`

| | |
|---|---|
| Role | `REQUESTER` (and the case's own requester) |
| Request | none |
| Response 200 | `CaseSummary` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403), `NOT_FOUND` (404), `ILLEGAL_STATE_TRANSITION` (409) |

Runs stages 0 to 15 synchronously through `app/services/orchestrator.py::process_case`. A case
not at `AUTHORIZATION_PREFLIGHT` raises `IllegalTransitionError`, so replaying processing is
HTTP 409 rather than a second run. Asserted by
`test_api.py::TestCaseLifecycle::test_reprocessing_a_completed_case_is_refused`.

A governance stop is **not** an HTTP error: the response is 200 with a `CaseSummary` whose
`current_state` is `CANNOT_PROCEED` and whose `reason_code` and `reason_message` carry the
closed reason. The stop is a governed outcome of the workflow, so it is reported as data. Any
of the fourteen stage failure codes in `STATE_FAILURE_REASON` may appear there.

#### `GET /api/v1/cases`

| | |
|---|---|
| Role | `REQUESTER` or `REVIEWER` (administrator denied) |
| Request | none |
| Response 200 | `CaseListResponse` — `{ cases: CaseSummary[] }` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403) |

Scoped to `business_scope_id`. A requester sees only its own cases; a reviewer sees the scope
minus cases it requested, so separation of duties applies to the listing as well as to the
action. An administrator is refused. Asserted by
`test_api.py::TestAccessControl::test_requester_sees_only_its_own_cases` and
`test_api.py::TestAccessControl::test_administrator_cannot_read_case_content`.

#### `GET /api/v1/cases/{case_id}`

| | |
|---|---|
| Role | any case-visible identity |
| Request | none |
| Response 200 | `CaseSummary` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403, administrator), `NOT_FOUND` (404) |

#### `GET /api/v1/cases/{case_id}/progress` — *beyond Section 13; serves the `/cases/:id/progress` UI route*

| | |
|---|---|
| Role | any case-visible identity |
| Request | none |
| Response 200 | `CaseProgressResponse` — `case`, `transitions[]`, `rule_results[]`, `limits[]`, `stop_record` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403), `NOT_FOUND` (404) |

`transitions` are `StateTransitionView` rows in sequence order (`sequence`, `from_state`,
`to_state`, `reason_code`, `reason_message`, `actor_id`, `occurred_at`). `rule_results` are
`RuleResultView` rows (`rule_id`, `rule_version`, `outcome`, `reason_code`, `effect`,
`precedence_rank`, `detail`, `evaluated_at`). `limits` is the register from
`app/domain/limits.py::limit_register_payload`. `stop_record` is the stored `StopRecord`
document or `null`.

#### `GET /api/v1/cases/{case_id}/packet`

| | |
|---|---|
| Role | any case-visible identity |
| Request | none |
| Response 200 | `PacketResponse` — `{ packet, canonical_sha256, seal_verified }` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403), `NOT_FOUND` (404 — includes `PACKET_NOT_AVAILABLE`), `CRITICAL_AUDIT_FAILURE` (422) |

`packet` is the canonical `DecisionReadinessPacket` document, whose exported schema is
`contracts/jsonschema/decision-readiness-packet-v1.json`. `seal_verified` is recomputed on
every read by `app/domain/canonical.py::verify_packet_hash`; it is not a stored flag.

Three refusals matter here. A case whose route is `CANNOT_PROCEED` returns
`PACKET_NOT_AVAILABLE` — a stop record is never rendered as a packet. A case with no packet
row returns the same code. A packet whose confirmed `PACKET_PRE_ISSUANCE` audit event is
missing or does not bind the packet id, version and issued hash raises
`CRITICAL_AUDIT_FAILURE` from `app/services/review.py::displayable_packet`, rather than being
displayed in a degraded form. A successful read appends a `PACKET_VIEWED` audit event.

#### `GET /api/v1/cases/{case_id}/audit`

| | |
|---|---|
| Role | any case-visible identity |
| Request | none |
| Response 200 | `AuditResponse` — `{ case_id, events: AuditEventView[], verification }` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403), `NOT_FOUND` (404) |

`AuditEventView` exposes `event_id`, `sequence`, `event_type`, `application_time`, `actor_id`,
`actor_kind`, `outcome`, `reason_code`, `severity`, `from_state`, `to_state`, `object_kind`,
`object_id`, `previous_event_hash`, `event_hash`, `confirmed`. The projection deliberately
exposes only the `binding` sub-object of the event payload, so no payload reference or free
text reaches the client. `verification` is
`contracts/jsonschema/audit-chain-verification-v1.json`, recomputed by
`app/services/audit.py::verify_chain` at read time.

#### `GET /api/v1/cases/{case_id}/lineage`

| | |
|---|---|
| Role | any case-visible identity |
| Request | none |
| Response 200 | `LineageResponse` — `{ case_id, nodes: LineageNode[], edges: LineageEdge[] }` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403), `NOT_FOUND` (404) |

Node kinds are `SOURCE`, `EXCERPT`, `CLAIM`, `RULE`, `ROUTE`, `PACKET`. Edge relations are
`RETRIEVED_AS`, `SUPPORTS` or `CITED_UNVERIFIED` (chosen by the stored `quote_verified` flag
on the claim–evidence link), `EVALUATED_BY`, `DETERMINES`, `SEALED_INTO`. The graph is derived
from persisted rows only; nothing is inferred at read time.

#### `GET /api/v1/evidence/{excerpt_id}`

| | |
|---|---|
| Role | any identity that can see the excerpt's case |
| Request | none |
| Response 200 | `ExcerptResponse` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403), `NOT_FOUND` (404) |

Fields: `excerpt_id`, `case_id`, `source_id`, `source_version`, `source_title`,
`authority_class`, `lifecycle`, `page_number`, `section_heading`, `char_start`, `char_end`,
`text`, `text_sha256`, `source_sha256`, `trust_label` (always the literal
`UNTRUSTED_CONTENT`), `citation_label`, `revocation_warning`.

Visibility is inherited through the excerpt's case, so evidence cannot be read across scopes
by guessing an excerpt id. Asserted by
`test_api.py::TestCaseLifecycle::test_evidence_endpoint_returns_the_exact_citation`.

#### `GET /api/v1/sources/{source_id}/pages/{page}`

| | |
|---|---|
| Role | `REQUESTER` or `REVIEWER` (administrator denied) |
| Request | path `source_id`, integer `page` |
| Response 200 | `SourcePageResponse` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403), `NOT_FOUND` (404), `SOURCE_QUARANTINED` (404) |

Fields: `source_id`, `source_version`, `title`, `lifecycle`, `page_number`, `page_count`,
`section_headings`, `char_start`, `char_end`, `text`, `trust_label`, `revocation_warning`.

Restricted to the caller's business scope, and quarantined source versions are never rendered
because their body text is instruction-like content. Asserted by
`test_api.py::TestCaseLifecycle::test_quarantined_source_page_is_not_rendered` and
`test_api.py::TestCaseLifecycle::test_source_page_renderer_is_read_only`.

### 4.4 Review

#### `GET /api/v1/review/queue` — *beyond Section 13; serves the `/review` UI route*

| | |
|---|---|
| Role | `REVIEWER` |
| Request | none |
| Response 200 | `CaseListResponse` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403) |

`app/services/review.py::review_queue` returns cases at `AWAITING_AUTHORIZED_HUMAN_REVIEW` in
the reviewer's scope, excluding any case the reviewer requested.

#### `POST /api/v1/cases/{case_id}/dispositions`

| | |
|---|---|
| Role | `REVIEWER` |
| Request | `DispositionRequest` — `disposition_value` (one of `ACCEPT_AS_TEST_EVIDENCE`, `REJECT_AS_TEST_EVIDENCE`, `RETURN_FOR_CLARIFICATION`), `human_rationale` (`RATIONALE_MIN_CHARS` = 20 to 4000 characters), optional `packet_sha256` matching `^[0-9a-f]{64}$` |
| Response 201 | `DispositionResponse` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403 — `ACCESS_DENIED`, `SEPARATION_OF_DUTIES_VIOLATION`, `REVIEWER_AUTHORITY_INVALID`), `NOT_FOUND` (404), `PACKET_NOT_AVAILABLE` (422 at stage 17 on hash mismatch; 404 when no displayable packet exists), `DISPOSITION_RATIONALE_REQUIRED` (422), `DISPOSITION_ALREADY_FINAL` (422), `CRITICAL_AUDIT_FAILURE` (422), `PACKET_CONTRACT_FAILURE` (422), `EMERGENCY_STOP_ACTIVE` (422) |

`DispositionResponse` fields: `case_id`, `disposition_id`, `disposition_value`, `is_final`,
`terminal_state`, `closure_event_id`, `packet_sha256`, `non_execution_notice`.

Three properties of this endpoint deserve stating explicitly:

- **There is no approving disposition value.** `app/domain/enums.py::DispositionValue` admits
  only the three test-only values above; an approval value does not exist to be sent. Asserted
  by `test_api.py::TestReviewApi::test_no_approval_disposition_value_exists`.
- **Every response carries a non-execution notice.** The `non_execution_notice` field is
  populated from the disposition record, so no caller can receive a disposition confirmation
  without it.
- **Failure returns the case to waiting, undisposed.** Any stop at stages 16 to 18 records a
  declared transition back to `AWAITING_AUTHORIZED_HUMAN_REVIEW` and leaves the packet
  displayable. Self-review is refused at the route by `sod_001`; asserted by
  `test_api.py::TestReviewApi::test_requester_self_review_is_denied_at_the_route`.

A `RETURN_FOR_CLARIFICATION` disposition is recorded, audited and resealed into the packet,
but is not final: `terminal_state` is `AWAITING_AUTHORIZED_HUMAN_REVIEW` and the case remains
open.

### 4.5 Administration

All four administrator operations require `AdminIdentity`. The administrator operates
controls: it cannot grant authorization, submit or review a case, modify source content, or
read case content. Asserted by
`test_api.py::TestAccessControl::test_requester_cannot_reach_administrator_routes`.

#### `GET /api/v1/admin/configuration`

| | |
|---|---|
| Role | `ADMINISTRATOR` |
| Request | none |
| Response 200 | `ConfigurationResponse` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403) |

Fields: `environment_id`, `component_versions`, `corpus_manifest_sha256`, `rule_catalog`,
`limits`, `state_machine`, `model_configurations`, `settings`, `prohibited_integrations`,
`kill_switch`, `status`.

This is an inspection surface, not a configuration surface: it is `GET` only, and nothing it
returns can be written back. `settings` is `Settings.redacted()`. `model_configurations`
exposes the pinned identifiers, prompt versions, schema ids, mode, `tool_calling_enabled`,
`fallback_enabled`, timeout, retry ceiling and the four status values — never an endpoint URL
or an API key. `status` is the fixed four-dimension block
(`built`/`integration` = `NOT_EVIDENCED`, `operational` = `NOT_EVIDENCED`,
`authorization` = `NOT_GRANTED`) which no request can change. Asserted by
`test_api.py::TestAdminApi::test_configuration_exposes_versions_without_secrets` and
`test_api.py::TestAdminApi::test_configuration_lists_the_prohibited_inventory`.

#### `POST /api/v1/admin/kill-switch`

| | |
|---|---|
| Role | `ADMINISTRATOR` |
| Request | `KillSwitchRequest` — `{ active, reason }` with a 10 to 500 character reason |
| Response 200 | `KillSwitchResponse` — `{ active, changed_at, changed_by, reason }` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403), `REQUEST_CONTRACT_INVALID` (422) |

Setting the switch halts intake, processing and disposition; clearing it restores them. Both
directions require a stated reason and are audited. Asserted by
`test_api.py::TestAdminApi::test_kill_switch_blocks_intake_and_can_be_cleared`.

#### `POST /api/v1/admin/audit/verify`

| | |
|---|---|
| Role | `ADMINISTRATOR` |
| Request | `AuditVerifyRequest` — `{ case_id? }`; omitted means the whole chain |
| Response 200 | `audit-chain-verification-v1` document |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403) |

`POST` rather than `GET` because it is an operator action that is itself recorded, not a
cacheable read. It recomputes hashes and reports divergence; it never repairs the chain.
Asserted by `test_api.py::TestAdminApi::test_audit_verification_endpoint`.

#### `POST /api/v1/admin/tevv/run`

| | |
|---|---|
| Role | `ADMINISTRATOR`, and `Settings.app_env` in `{local, demo, test}` |
| Request | `TevvRunRequest` — `{ scenario_ids?: string[] }`; empty means the full frozen matrix |
| Response 200 | `TevvRunResponse` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403, including the environment gate), `REQUEST_CONTRACT_INVALID` (422) |

The request can name scenario ids and nothing else. **It cannot supply a fault profile, a
model configuration, a rule outcome or an expected result**; fault injection exists only as a
service-layer argument to `app/services/orchestrator.py::ProcessOptions`, set by
`app/services/tevv.py` and unreachable from HTTP. See `docs/tevv-plan.md`.

#### `GET /api/v1/admin/tevv/runs/{tevv_run_id}`

| | |
|---|---|
| Role | `ADMINISTRATOR` |
| Request | none |
| Response 200 | `TevvRunResponse` |
| Reason codes | `REQUESTER_OR_SESSION_INVALID` (401), `ACCESS_DENIED` (403), `NOT_FOUND` (404) |

`TevvRunResponse` fields: `tevv_run_id`, `plan_version`, `executor`, `started_at`,
`completed_at`, `component_versions`, `summary`, `results[]`. Each `TevvResultView` carries
`scenario_id`, `title`, `category`, `repetition`, `status`, `expected`, `actual`, `case_id`,
`trace_id`, `defect_ids`, `executed_at`. Asserted by
`test_api.py::TestAdminApi::test_tevv_run_and_fetch`.

---

## 5. Contract stability

`contracts/openapi.json` and the 27 documents in `contracts/jsonschema/` are committed
artefacts, not generated at request time.
`test_contracts.py::TestExportedJsonSchemas::test_schemas_are_current` regenerates them and
fails if the committed files differ, so a change to a Pydantic model that is not re-exported
breaks the suite.
`test_contracts.py::TestExportedJsonSchemas::test_every_schema_is_valid_draft_2020_12` validates
each document, and
`test_contracts.py::TestExportedJsonSchemas::test_packet_schema_forbids_additional_properties`
confirms the packet schema is closed.

---

## 6. Related documents

| Document | Covers |
|---|---|
| `docs/architecture.md` | Trust boundaries, the component map, the request lifecycle, stack deviations |
| `docs/rule-catalog.md` | The 15 rules and the reason code each produces |
| `docs/source-governance.md` | The corpus behind the evidence and source-page endpoints |
| `docs/model-configuration-card.md` | What the model gateway will and will not accept |
| `docs/threat-model.md` | The threats these controls contain, and the residual risk |
| `docs/tevv-plan.md` | The frozen scenario matrix behind the TEVV endpoints |

---

| Dimension | Value |
|---|---|
| Built | `NOT_EVIDENCED` |
| Integration | `NOT_EVIDENCED` |
| Operational | `NOT_EVIDENCED` |
| Authorization | `NOT_GRANTED` |
