# Independent Code Review Record — NABD AI Decision Review

## 0. Template control block

| Field | Value |
|---|---|
| Template ID | `TPL-CODE-REVIEW-V1` |
| Template version | `1.0.0` |
| Template kind | `CONTROL_ARTIFACT` |
| Assurance gate | `G-B — Independent code review` |
| Environment | `ISOLATED_PROTOTYPE_V1` |
| Data boundary | `SYNTHETIC_ONLY` |
| Business scope | `BUSINESS_UNIT_V1` |
| Controlling specification | `docs/NABD_AI_CURSOR_FULL_PROTOTYPE_BUILD_SPEC.md`, Sections 3, 7.1, 17, 17.1, 17.2 |
| Preceding gate | `G-A — Developer verification` |
| Following gate | `G-C — Independent security testing` |
| Completion state | `<PENDING>` |

> **Control artifact notice.** This template is a control artifact. It does not itself constitute evidence, and its presence in the repository does not indicate that a review has been performed, that any finding has been resolved, or that any status dimension has changed. Evidence exists only when a named, independent reviewer has completed every field below against a specific component version set and has attached the raw underlying records.

### 0.1 Placeholder tokens

Every cell in this document must carry a value before the record is considered complete. An unpopulated cell is read as `<NOT_ASSESSED>` and never as a pass.

| Token | Meaning |
|---|---|
| `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | The named reviewer in the independent evaluator function must supply the value. |
| `<TO BE COMPLETED BY TECHNICAL OWNER>` | The technical owner supplies the value as an input to the review; the reviewer verifies it. |
| `<PENDING>` | Not yet determined. |
| `<NOT_ASSESSED>` | The item has not been examined. Default for every checklist result. |
| `<NOT_RUN>` | The supporting activity has not been executed. |
| `<NONE_RECORDED>` | Deliberately empty at completion time; must be affirmed by the completer, not left by default. |
| `<NOT_APPLICABLE: reason>` | Requires a written reason. A bare `NOT_APPLICABLE` is invalid. |

---

## 1. Reviewer independence declaration

### 1.1 Three-function separation (Section 17)

The three-function separation is mandatory and applies to this record.

- The **technical owner** prepares code and developer evidence.
- The **independent evaluator or reviewer** reviews code, security, TEVV and deployment results.
- The **human owner or delegate** accepts or rejects a narrow evidence or status claim.

One identity must not perform all three functions for the same component, version, status dimension and evidence set. Invariant INV-16 prohibits self-acceptance: a developer, model, evaluator, administrator or evidence record cannot accept its own status claim. Under the gate G-B independence rule, the reviewer did not author the reviewed changes and cannot be the sole acceptor of any status claim.

### 1.2 Declaration by the reviewer

| Declaration | Reviewer response |
|---|---|
| Reviewer name | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |
| Reviewer role and organisational relationship to the technical owner | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |
| Reviewer contact reference | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |
| I did not author, co-author or commit any change in the reviewed diff range | `<TO BE COMPLETED BY INDEPENDENT REVIEWER: CONFIRMED / NOT_CONFIRMED + explanation>` |
| I am not the human owner or delegate who will accept the resulting status claim | `<TO BE COMPLETED BY INDEPENDENT REVIEWER: CONFIRMED / NOT_CONFIRMED + explanation>` |
| I have no interest that would be served by understating a finding | `<TO BE COMPLETED BY INDEPENDENT REVIEWER: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Any exception to independence, and the compensating control applied | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |

| Function | Named identity | Distinct from the other two functions |
|---|---|---|
| Technical owner (prepared the code and developer evidence) | `<TO BE COMPLETED BY TECHNICAL OWNER>` | `<PENDING>` |
| Independent reviewer (this record) | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<PENDING>` |
| Human owner or delegate (accepts or rejects the narrow claim) | `<PENDING>` | `<PENDING>` |

If any two rows above name the same identity for the same component, version, status dimension and evidence set, the review is invalid and must be reassigned.

---

## 2. Review scope and version identification

### 2.1 Scope statement

| Field | Value |
|---|---|
| Review scope, stated as an explicit boundary | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |
| Explicitly out of scope for this review | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |
| Repository | `nabd-ai-prototype` |
| Repository remote reference | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Branch reviewed | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Base commit SHA of the diff range | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Head commit SHA of the diff range | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Exact diff command used to reproduce the review set | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |
| Files in the diff range (count) | `<PENDING>` |
| Files actually examined (count) | `<PENDING>` |
| Files in the diff range not examined, with reason | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |
| Review start (UTC) | `<PENDING>` |
| Review end (UTC) | `<PENDING>` |
| Review effort recorded | `<PENDING>` |

### 2.2 Component version identification

Every version below must be recorded exactly. A review is bound to the version set it examined and does not carry forward to any other version set.

| Component | Identifier expected in the authorization fixture | Version reviewed |
|---|---|---|
| Workflow / finite-state machine | `workflow` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Domain schema set | `schema` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Canonical JSON profile | `canonical_json_profile` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Rule catalog | `rule_catalog` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Frozen synthetic corpus | `corpus` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Corpus manifest SHA-256 | `source_manifest_sha256` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Retrieval configuration | `retrieval` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Draft prompt | `prompt_draft` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Verifier prompt | `prompt_verify` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Packet schema | `packet_schema` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Audit chain profile | `audit_chain` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Use-case contract | `use_case_contract` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Draft model configuration ID | — | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Verifier model configuration ID | — | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Active `MODEL_MODE` at review time | — | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| API application version | — | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Web application version | — | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Container image digests (`db`, `api`, `web`) | — | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Dependency lockfile hashes | — | `<TO BE COMPLETED BY TECHNICAL OWNER>` |

| Version-consistency check | Result |
|---|---|
| Every version above appears in the `SYNTHETIC_DEMO_AUTHORIZATION` allowed component version set | `<NOT_ASSESSED>` |
| No component was changed between the recorded head commit and the review end time | `<NOT_ASSESSED>` |

---

## 3. Review checklist

Result vocabulary for every row: `CONFORMS`, `DOES_NOT_CONFORM`, `PARTIAL`, `NOT_APPLICABLE: reason`, `NOT_ASSESSED`. The default is `NOT_ASSESSED`. `CONFORMS` may be recorded only where the reviewer has inspected the implementing code and can cite the file and line range in the evidence column.

### 3.1 Permanent product invariants (Section 3)

| ID | Checklist item | Result | Evidence reference (file, line range, commit) | Finding ID |
|---|---|---|---|---|
| CR-INV-01 | INV-01: no model, score, document, administrator or packet grants institutional authority in code | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-02 | INV-02: server validates the exact synthetic authorization fixture before any processing | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-03 | INV-03: a finite-state machine owns all transitions; the model cannot select states or tools | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-04 | INV-04: source eligibility and exact retrieval complete before any model call | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-05 | INV-05: user text, documents, metadata, excerpts, outputs and errors remain in data-plane fields | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-06 | INV-06: a deterministic rule failure always outranks model confidence or reviewer preference | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-07 | INV-07: every material claim carries exact eligible citations or causes a stop | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-08 | INV-08: gaps, ambiguities, conflicts and limits are packet objects and route inputs | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-09 | INV-09: absence, conflict, stale data, malformed output, timeout and unavailability return a reason-coded stop | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-10 | INV-10: canonical typed JSON is authoritative; free-text answers are subordinate | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-11 | INV-11: reviewer identity, current role, scope, relationship and separation of duties are server-verified | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-12 | INV-12: no disposition triggers a connector, workflow, write, message, approval or transaction | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-13 | INV-13: packet display and disposition closure require different confirmed audit events | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-14 | INV-14: four separate status dimensions; no generic or merged readiness state is rendered anywhere | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-15 | INV-15: local, hosted, on-premises and offline deployment share the non-execution rule | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-INV-16 | INV-16: no code path allows a developer, model, evaluator, administrator or record to accept its own status claim | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.2 Architecture and trust boundaries (Section 5)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-ARC-01 | Logical boundaries between P0–P7 remain explicit in code, contracts, permissions, database tables, tests and documentation | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-ARC-02 | Control plane holds authorization fixtures, use-case contract, roles, eligibility metadata, frozen rules, numeric limits, transitions, schemas and version configuration only | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-ARC-03 | No data-plane field can write into a control-plane field, directly or by deserialisation | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-ARC-04 | The authorization gate precedes source registry and eligibility on every path | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-ARC-05 | Quarantine and content isolation sit between the frozen corpus and source eligibility | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-ARC-06 | There is no edge, client, queue or adapter from packet or disposition to any operational system | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.3 Schemas, enumerations and canonicalization (Section 7)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-SCH-01 | Every privileged boundary uses JSON Schema and Pydantic models with `extra = forbid` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SCH-02 | No arbitrary dictionaries, untyped JSON or model-produced control fields are accepted | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SCH-03 | Enumerations match Section 7.1 exactly, with no added, renamed or removed values | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SCH-04 | All fourteen core objects in Section 7.2 exist as versioned schemas | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SCH-05 | Every record carries stable ID, schema version, created timestamp, case ID, data classification, actor or service provenance, and lineage references | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SCH-06 | The packet contains every required section listed in Section 7.2, and disposition only after a valid review | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SCH-07 | `nabd-canonical-json-v1` implements sorted keys, compact separators, ISO-8601 UTC with `Z`, `\n` line endings, no floating-point risk scores, Unicode NFC | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SCH-08 | The hash preimage omits only `integrity.packet_sha256`, and `packet.integrity` stores profile ID, hash, calculation time and verifier method | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SCH-09 | No code, comment, schema description or user-facing string describes the seal as proof of truth, immutable storage, authorization or authorship | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.4 Database and persistence rules (Section 8)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-DB-01 | Case identity is a sortable UUID generated once at intake and propagated everywhere | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-DB-02 | Confirmed audit events reject `UPDATE` and `DELETE` through both database role permissions and a PostgreSQL trigger | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-DB-03 | A packet correction creates a new immutable packet version; prior versions remain retrievable under access rules | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-DB-04 | Only manifest-listed active source versions are eligible | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-DB-05 | Every query scopes by case, business unit, identity and source access before returning content | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-DB-06 | A unique constraint permits one final accepted or rejected test disposition per exact packet version, and attempts remain auditable | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-DB-07 | The transition table stores from-state, to-state, reason, actor or service, and applicable component and rule versions | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-DB-08 | Soft revocation prevents future use immediately while historical records retain dated facts with warnings | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-DB-09 | Repositories separate read and write functions; there is no generic ORM update endpoint | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-DB-10 | Each state transition and its required audit event share one transaction; a failed audit confirmation rolls back or routes to `CANNOT_PROCEED` before display or closure | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.5 Corpus governance and retrieval (Section 9)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-SRC-01 | The corpus is created during build or seed and never by runtime upload | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SRC-02 | Seeding fails when a manifest item does not match its source file hash | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SRC-03 | `SourceRecord` carries owner, authority class, version, source hash, effective period, lifecycle, business scope, permitted use case, access labels, source path, page structure and integrity reference | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SRC-04 | The parser retains source ID, version, page number, section heading, paragraph or block index, character offsets, extracted-text hash and original document hash | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SRC-05 | Retrieved content is always marked `UNTRUSTED_CONTENT` and a citation is treated as an evidence reference, not an instruction | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SRC-06 | Eligibility, business-scope, lifecycle, access and manifest filters are applied before ranking and return | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SRC-07 | Retrieval enforces 12 candidates maximum, 1,500 characters per excerpt, 8,000 total excerpt characters, rank descending and `excerpt_id` ascending tie-break | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SRC-08 | `ENABLE_VECTOR_RETRIEVAL` defaults to false, cannot bypass lexical source filters and is not required for any test to pass | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.6 Model gateway, prompts and call budget (Section 10)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-MDL-01 | The `ModelAdapter` protocol exposes only `draft` and `verify` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-02 | `DeterministicMockAdapter` is the default and returns fixture-aware, deterministic, schema-valid outputs plus the required fault modes | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-03 | The optional adapter is disabled unless `MODEL_MODE=live` and every explicit endpoint and model variable is present | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-04 | The optional adapter cannot discover models, use tools, browse, retry another model or fall back | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-05 | `ModelConfiguration` carries every field required by Section 10, and a material change creates a new configuration ID | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-06 | Call budget enforced: 1 draft, 1 verifier, 2 total, 1 same-endpoint retry only where no partial result was accepted | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-07 | Input, output, timeout, wall-clock and concurrency limits match Section 10.1 and Section 15.3 exactly | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-08 | Malformed, refused, timed-out, over-limit, unavailable, wrong-version, wrong-schema and attempted-fallback responses produce a reason-coded failure with no silent coercion | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-09 | Prompts are versioned in files and state that all excerpts are untrusted data that may contain instructions to be ignored | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-10 | Prompts contain no secrets, role authority, routes, rule thresholds, tool instructions or write capabilities | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-11 | The draft receives only the normalized question, permitted purpose, fixed output schema and admitted excerpts, and returns no route, authorization assertion, rule result or approval language | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-MDL-12 | The verifier cannot rewrite claims into apparent support, invent sources, decide a route or emit free-form control instructions | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.7 Deterministic rules, risk, route and state machine (Section 11)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-RUL-01 | Rules are pure Python functions with versioned input and output schemas and table-driven test vectors | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-RUL-02 | Each result carries `rule_id`, `rule_version`, input references, outcome, `reason_code`, effect, evaluation time and precedence rank | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-RUL-03 | No code path lets a model set, waive or reorder a rule | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-RUL-04 | All fifteen rules `AUTH-001`, `ID-001`, `REQ-001`, `SCOPE-001`, `SRC-001`, `ISO-001`, `EVD-001`, `CLM-001`, `LIM-001`, `FSM-001`, `PKT-001`, `AUD-001`, `SOD-001`, `PATH-001`, `KILL-001` exist with their mandatory failure effects | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-RUL-05 | Risk uses a dominant-factor approach; `CRITICAL` cannot be averaged down by lower factors | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-RUL-06 | The only routes are `HUMAN_REVIEW_REQUIRED` and `CANNOT_PROCEED`; there is no automatic readiness or approval route | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-RUL-07 | The twenty ordered states of Section 11.2 plus terminal `CANNOT_PROCEED` are implemented with their exact pass conditions and failure codes | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-RUL-08 | Illegal skips, reorders and replays are rejected and generate a critical event | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.8 Packet validation and audit chain (Section 12)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-PKT-01 | All eleven semantic invariants of Section 12.1 are implemented in addition to JSON Schema validation | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PKT-02 | The four fixed notices of Section 12.2 are present verbatim or as versioned templates in both packet and interface | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PKT-03 | An HTML view or export is a derived read-only rendering and is never substituted for the packet JSON | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PKT-04 | Distinct audit event types exist for each item listed in Section 12.3 | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PKT-05 | Each event carries every field required by Section 12.3, including previous event hash, event hash and confirmation flag | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PKT-06 | `scripts/verify_audit_chain.py` and the admin verification endpoint recompute the chain and report the first divergence | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PKT-07 | Packet display requires a confirmed pre-issuance event whose packet ID, version and hash match exactly | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PKT-08 | A final disposition requires reverified reviewer authority, no self-review, non-empty human rationale, exact packet version and hash, and a later closure event | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PKT-09 | No packet or disposition can hold an action ID, webhook URL, external target, operational record mutation, or approval or execution command | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.9 API contract (Section 13)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-API-01 | Every error uses the single envelope and no error leaks secrets, prompts, credentials, hidden control settings or unauthorized case content | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-API-02 | Every path in the Section 13 table exists with the stated behaviour and no additional privileged path exists | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-API-03 | Role restrictions are server-derived from the signed demo session; the browser cannot submit role, scope, authority or separation-of-duties fields | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-API-04 | No generic CRUD API exists for authorization, source governance, rules, model configuration, status acceptance or production users | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-API-05 | Health endpoints report liveness and dependency readiness without sensitive detail | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.10 Security-relevant code (Section 15)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-SEC-01 | Automated assertions exist for every row of the Section 15.1 prohibited-connection inventory | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SEC-02 | The instruction-like content detector is a deterministic pattern or heuristic fixture set used as defence in depth, and is not a source-authority decision-maker | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SEC-03 | No third model-based detector was introduced | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SEC-04 | Model output never reaches code execution, shell commands, SQL, URLs, templates, access-control fields, state transition functions or any connector | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SEC-05 | SQL is parameterized, rendered document text is escaped, CSP and secure HTTP headers are set, and all path parameters are validated | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SEC-06 | Request-size, time and concurrency limits are applied and logs are redacted | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SEC-07 | No API key or secret appears in code, test fixtures, logs, packets, screenshots or prompts, and `.env.example` contains placeholders only | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-SEC-08 | The container runs successfully with no outbound internet access in the default mock mode | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.11 Manual prohibited-path inspection (gate G-B minimum activity)

This subsection must be completed by direct inspection, not by relying on the automated suite. Record the exact commands or searches used.

| ID | Prohibited path inspected | Method and command used | Result | Evidence reference | Finding ID |
|---|---|---|---|---|---|
| CR-PP-01 | Email, SMS, chat or notification SDK, dependency, route or configuration | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PP-02 | Webhook or generic outbound HTTP action client | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PP-03 | Public web search, browser or scraper dependency or route | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PP-04 | Payment, procurement or transaction dependency, route or schema field | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PP-05 | Operational database write path or external DSN configuration | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PP-06 | Repository mutation, upload endpoint or dynamic source ingestion; runtime writability of the source directory | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PP-07 | OAuth or real identity provider integration | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PP-08 | External telemetry or crash reporting | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PP-09 | Model tool or function calling configuration; output schema acceptance of a tool request | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-PP-10 | Provider or model fallback configuration | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.12 Interface, brand and accessibility code (Section 14)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-UI-01 | Every required route in Section 14.1 exists with the stated capability | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-UI-02 | Status is never colour-only; each status carries text, icon and shape | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-UI-03 | No generic green approved indicator, merged status or readiness badge appears in any view | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-UI-04 | Evidence views are read-only with no edit control | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-UI-05 | Client validation mirrors but does not replace server rules | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-UI-06 | English and Arabic are supported with layout mirroring, Unicode directionality and readable Arabic line height | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-UI-07 | Keyboard navigation, focus indicators, reflow and text scaling, grayscale legibility, reduced-motion preference and WCAG 2.2 AA contrast are implemented | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-UI-08 | No prohibited marketing claim appears in interface copy, translation files or documentation strings | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-UI-09 | The four fixed notices render in the packet view | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.13 Tests, quality gates and status reporting (Sections 6, 19, 20)

| ID | Checklist item | Result | Evidence reference | Finding ID |
|---|---|---|---|---|
| CR-TST-01 | No quality gate can be skipped silently in local or CI execution | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-TST-02 | Rule-vector, replay, audit-chain, security and TEVV tests exist and are runnable | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-TST-03 | Migration, rollback and audit mutation-denial tests exist | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-TST-04 | `PROTOTYPE_STATUS.md` lists exact component versions and four separate status fields and makes no operational or authorization claim | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-TST-05 | `SECURITY_BOUNDARIES.md` lists every dependency and endpoint | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |
| CR-TST-06 | Any stack substitution is recorded in `docs/architecture.md` and `PROTOTYPE_STATUS.md` | `<NOT_ASSESSED>` | `<PENDING>` | `<NONE_RECORDED>` |

### 3.14 Checklist completion summary

Percentages alone are not an acceptable summary. Record exact counts.

| Measure | Numerator | Denominator | Value |
|---|---|---|---|
| Checklist rows recorded as `CONFORMS` | `<PENDING>` | `<PENDING>` | `<NOT_ASSESSED>` |
| Checklist rows recorded as `DOES_NOT_CONFORM` | `<PENDING>` | `<PENDING>` | `<NOT_ASSESSED>` |
| Checklist rows recorded as `PARTIAL` | `<PENDING>` | `<PENDING>` | `<NOT_ASSESSED>` |
| Checklist rows recorded as `NOT_APPLICABLE` with written reason | `<PENDING>` | `<PENDING>` | `<NOT_ASSESSED>` |
| Checklist rows remaining `NOT_ASSESSED` | `<PENDING>` | `<PENDING>` | `<NOT_ASSESSED>` |

---

## 4. Findings register

One row per finding. Every `DOES_NOT_CONFORM` or `PARTIAL` checklist result must produce at least one finding. Every finding must also be recorded in `artifacts/templates/defect_register.csv` when it requires a code correction.

| Finding ID | Checklist ID | Severity | Location (file, line range) | Description of the non-conformance | Invariant, rule or section breached | Required correction | Defect register ID | Status |
|---|---|---|---|---|---|---|---|---|
| `EXAMPLE-000` | `<PENDING>` | `<PENDING>` | `<PENDING>` | ILLUSTRATIVE ROW ONLY. Remove before use. This row records no finding and no result. | `<PENDING>` | `<PENDING>` | `EXAMPLE-000` | `<PENDING>` |
| `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

Finding status vocabulary: `OPEN`, `IN_ANALYSIS`, `CORRECTION_IN_PROGRESS`, `AWAITING_RE_REVIEW`, `RE_REVIEW_FAILED`, `CLOSED_CORRECTED`, `CLOSED_NOT_A_DEFECT`, `DEFERRED_FUTURE_GATED`. The default for a newly raised finding is `OPEN`.

### 4.1 Severity assignment

Severity uses the Section 7.1 `Severity` enumeration exactly.

| Severity | Assignment criterion for this gate |
|---|---|
| `S0_CRITICAL` | A prohibited external action or connection path, a cross-scope disclosure, an invalid-authority or separation-of-duties-invalid disposition, a material unsupported claim presented as definitive, a deterministic-control bypass, or a critical-audit bypass. |
| `S1_HIGH` | A control that is present but circumventable, an invariant enforced only by prompt wording, a missing mandatory stop, or a defect that would produce one of the `S0_CRITICAL` outcomes under a plausible variation. |
| `S2_MODERATE` | A defect that degrades evidence quality, traceability, determinism or accessibility without defeating a control. |
| `S3_LOW` | A defect in clarity, naming, documentation or non-control code with no effect on a control boundary. |

Any unresolved `S0_CRITICAL` or `S1_HIGH` finding blocks acceptance of the affected release and blocks movement to the next assurance gate.

| Severity | Count raised | Count open | Count closed |
|---|---|---|---|
| `S0_CRITICAL` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `S1_HIGH` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `S2_MODERATE` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `S3_LOW` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

---

## 5. Review disposition

The reviewer records exactly one disposition. The disposition concerns the code review only. It does not set a status dimension, does not accept evidence, and does not authorize anything.

| Disposition value | Meaning |
|---|---|
| `REVIEW_NOT_STARTED` | No review activity has occurred. Default. |
| `REVIEW_IN_PROGRESS` | Review is under way and incomplete. |
| `REVIEW_BLOCKED` | The reviewer cannot proceed; the blocking condition must be recorded. |
| `CORRECTIONS_REQUIRED` | One or more findings must be corrected before the review can conclude. |
| `RE_REVIEW_REQUIRED` | Corrections have been submitted and require a further review round. |
| `REVIEW_CONCLUDED_WITH_OPEN_FINDINGS` | The review round is complete and findings remain open. The open findings and their severities must be listed. |
| `REVIEW_CONCLUDED_NO_OPEN_FINDINGS` | The review round is complete and no finding remains open at the recorded version set. This is a statement about the review round only. |

| Field | Value |
|---|---|
| Selected disposition | `REVIEW_NOT_STARTED` |
| Basis for the disposition, in the reviewer's own words | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |
| Blocking condition, if `REVIEW_BLOCKED` | `<NOT_APPLICABLE: reason required if selected>` |
| Open findings at disposition time, by ID and severity | `<PENDING>` |
| Limits of this review that a later reader must know | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |

---

## 6. Re-review record

Failed evidence is retained visibly and is never overwritten. Add one row per re-review round; do not edit earlier rows.

| Round | Date (UTC) | Reviewer | Commit range re-reviewed | Findings retested (IDs) | Findings closed (IDs) | Findings still open (IDs) | New findings raised (IDs) | Round outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | `<PENDING>` | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| 2 | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

| Field | Value |
|---|---|
| Location of retained superseded review rounds | `<PENDING>` |
| Confirmation that no earlier round was overwritten | `<TO BE COMPLETED BY INDEPENDENT REVIEWER: CONFIRMED / NOT_CONFIRMED + explanation>` |

---

## 7. Status dimensions

The four dimensions are independent and are recorded separately. They must never be merged, averaged or rendered as a single readiness state (INV-14).

| Dimension | Permitted values (Section 7.1) | Default | Current value |
|---|---|---|---|
| Built | `NOT_EVIDENCED` / `PARTIALLY_EVIDENCED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` |
| Integration | `NOT_EVIDENCED` / `PARTIALLY_EVIDENCED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` |
| Operational | `NOT_EVIDENCED` / `HISTORICAL_CONFIRMED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` |
| Authorization | `NOT_GRANTED` / `GRANTED_WITH_CONDITIONS` / `GRANTED` | `NOT_GRANTED` | `NOT_GRANTED` |

Gate G-B produces code-review evidence only. Completing this record does not change any dimension above. A dimension changes only when a human owner or delegate records a decision in a completed `human_owner_acceptance_record.md`, and Operational and Authorization remain at their defaults for `ISOLATED_PROTOTYPE_V1`.

---

## 8. Evidence retained for this gate

| Evidence item | Artifact path | SHA-256 | Recorded in `release_evidence_index.json` |
|---|---|---|---|
| Completed review checklist (this document) | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| Review comments and findings export | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| Commit links for the reviewed diff range | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| Resolution and re-review record | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| Manual prohibited-path inspection transcript | `<PENDING>` | `<PENDING>` | `<PENDING>` |

---

## 9. Signature and date

Signing attests only to the accuracy of the record above. It is not an acceptance of any status claim, and it confers no authority.

| Field | Value |
|---|---|
| Reviewer name | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |
| Reviewer function | Independent evaluator or reviewer |
| Signature | `<TO BE COMPLETED BY INDEPENDENT REVIEWER>` |
| Date signed (UTC) | `<PENDING>` |
| Component version set to which this signature is bound | `<PENDING>` |
| Countersigning technical owner (acknowledgement of receipt only) | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Date acknowledged (UTC) | `<PENDING>` |
| Next assurance gate | `G-C — Independent security testing` |

A completed instance of this record must be stored as an immutable artifact, listed in `artifacts/templates/evidence_register.csv`, and indexed in `artifacts/templates/release_evidence_index.json` before gate G-F is convened.
