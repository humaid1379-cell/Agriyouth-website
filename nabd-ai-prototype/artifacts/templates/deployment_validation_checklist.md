# Deployment Validation Checklist — NABD AI Decision Review

## 0. Template control block

| Field | Value |
|---|---|
| Template ID | `TPL-DEPLOYMENT-VALIDATION-CHECKLIST-V1` |
| Template version | `1.0.0` |
| Template kind | `CONTROL_ARTIFACT` |
| Assurance gate | `G-E — Deployment validation` |
| Environment | `ISOLATED_PROTOTYPE_V1` |
| Data boundary | `SYNTHETIC_ONLY` |
| Business scope | `BUSINESS_UNIT_V1` |
| Controlling specification | `docs/NABD_AI_CURSOR_FULL_PROTOTYPE_BUILD_SPEC.md`, Sections 3, 7.1, 17, 17.1, 17.2, 18 |
| Preceding gate | `G-D — TEVV` |
| Following gate | `G-F — Human-owner evidence acceptance` |
| Completion state | `<PENDING>` |

> **Control artifact notice.** This template is a control artifact. It does not itself constitute evidence, and its presence in the repository does not indicate that a clean-environment validation has been performed, that any confirmation has been satisfied, or that any status dimension has changed. Evidence exists only when a named, separate validator has completed every row below in a clean environment and has attached the transcript, logs and hashes.

> **Scope limitation.** Completing this checklist supports deployment-validation evidence for an isolated prototype only. It does not establish Operational status, service monitoring, incident response maturity, customer data approval, or authorization to use the prototype outside its synthetic environment. Deployment does not change authority (INV-15).

### 0.1 Placeholder tokens

Every cell must carry a value before the checklist is considered complete. An unpopulated cell is read as `<NOT_RUN>` and never as a pass.

| Token | Meaning |
|---|---|
| `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | The named validator in the independent evaluator function must supply the value. |
| `<TO BE COMPLETED BY TECHNICAL OWNER>` | The technical owner supplies the value as an input; the validator verifies it. |
| `<PENDING>` | Not yet determined. |
| `<NOT_RUN>` | The confirmation has not been executed. Default for every result. |
| `<NOT_ASSESSED>` | The item has not been examined. |
| `<NONE_RECORDED>` | Deliberately empty at completion time; must be affirmed by the completer. |
| `<NOT_APPLICABLE: reason>` | Requires a written reason. A bare `NOT_APPLICABLE` is invalid. |

Result vocabulary for every confirmation: `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`. The default is `NOT_RUN`. `PASS` may be recorded only where a transcript or log has been attached and hashed, and the evidence link column resolves.

---

## 1. Validator independence declaration

### 1.1 Three-function separation (Section 17)

- The **technical owner** prepares code and developer evidence.
- The **independent evaluator or reviewer** reviews code, security, TEVV and deployment results.
- The **human owner or delegate** accepts or rejects a narrow evidence or status claim.

One identity must not perform all three functions for the same component, version, status dimension and evidence set. Invariant INV-16 prohibits self-acceptance: a developer, model, evaluator, administrator or evidence record cannot accept its own status claim. Under the gate G-E independence rule the validation is performed by a separate validator or in a clean environment; where a separate validator is not available, the clean-environment condition and its verification must be recorded below.

### 1.2 Declaration by the validator

| Declaration | Validator response |
|---|---|
| Validator name | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Validator role and organisational relationship to the technical owner | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| I am a separate validator from the technical owner | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR: CONFIRMED / NOT_CONFIRMED + explanation>` |
| The environment was clean: no pre-existing build cache, database volume, image layer, seeded corpus or credential from a prior run was reused | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Method used to establish and verify the clean condition | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| I am not the human owner or delegate who will accept the resulting status claim | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR: CONFIRMED / NOT_CONFIRMED + explanation>` |
| No real, personal, customer, confidential, institutional, clinical, legal, financial or production data or credential was used | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Any exception to independence, and the compensating control applied | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |

| Function | Named identity | Distinct from the other two functions |
|---|---|---|
| Technical owner | `<TO BE COMPLETED BY TECHNICAL OWNER>` | `<PENDING>` |
| Deployment validator (this checklist) | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` |
| Human owner or delegate | `<PENDING>` | `<PENDING>` |

---

## 2. Environment manifest

| Field | Value |
|---|---|
| Validation run ID | `<PENDING>` |
| Validation start (UTC) | `<PENDING>` |
| Validation end (UTC) | `<PENDING>` |
| Host operating system, kernel and architecture | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Container runtime and version | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Compose version | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Clean checkout remote and commit SHA | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Working tree confirmed clean at validation start | `<NOT_RUN>` |
| `MODEL_MODE` used for the primary validation pass | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| `ENABLE_VECTOR_RETRIEVAL` value observed | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Network posture applied (egress policy, DNS, proxy) | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Method used to observe and record egress attempts | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Local volumes created for database and artifacts | `<PENDING>` |
| Source corpus mount mode observed at runtime | `<PENDING>` |
| Database port exposure observed | `<PENDING>` |
| Container user and privilege configuration observed | `<PENDING>` |
| Environment teardown and data destruction record | `<PENDING>` |

### 2.1 Image and artifact hash register

| Item | Tag or reference | Digest or SHA-256 | Source of the value | Verified by the validator |
|---|---|---|---|---|
| `db` image | `<TO BE COMPLETED BY TECHNICAL OWNER>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` |
| `api` image | `<TO BE COMPLETED BY TECHNICAL OWNER>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` |
| `web` image | `<TO BE COMPLETED BY TECHNICAL OWNER>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` |
| Python lockfile | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` |
| JavaScript lockfile | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` |
| Corpus manifest | `data/synthetic_policy_collection_v1/manifest.json` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` |
| Evidence bundle produced by `make evidence-bundle` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` |
| Validation transcript | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` |

### 2.2 Version configuration fingerprints

Recorded from `GET /api/v1/admin/configuration`. No secret value may be recorded here.

| Component | Fingerprint reported by the running system | Matches the authorization fixture allowed set |
|---|---|---|
| Workflow | `<PENDING>` | `<NOT_RUN>` |
| Schema set | `<PENDING>` | `<NOT_RUN>` |
| Canonical JSON profile | `<PENDING>` | `<NOT_RUN>` |
| Rule catalog | `<PENDING>` | `<NOT_RUN>` |
| Corpus and manifest SHA-256 | `<PENDING>` | `<NOT_RUN>` |
| Retrieval configuration | `<PENDING>` | `<NOT_RUN>` |
| Draft prompt | `<PENDING>` | `<NOT_RUN>` |
| Verifier prompt | `<PENDING>` | `<NOT_RUN>` |
| Packet schema | `<PENDING>` | `<NOT_RUN>` |
| Audit chain profile | `<PENDING>` | `<NOT_RUN>` |
| Use-case contract | `<PENDING>` | `<NOT_RUN>` |
| Model configuration IDs | `<PENDING>` | `<NOT_RUN>` |

---

## 3. Clean-environment confirmations (Section 18)

These are the twelve confirmations required by Section 18. Every row must be executed in the clean environment described in Section 2 above. A row may not be removed, merged or reordered.

| # | Confirmation required in a clean environment | Method and exact command used | Evidence link | Evidence SHA-256 | Result | Notes and observed reason codes |
|---:|---|---|---|---|---|---|
| 1 | The project builds from a clean checkout using lockfiles and documented commands. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 2 | Database migrations and frozen corpus seed complete and validate manifest hashes. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 3 | Default mock mode starts without network credentials or outbound model access. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 4 | No prohibited connectors, packages, routes or configuration fields are present. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 5 | Optional live mode allows only one named endpoint and fails closed when unavailable. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 6 | `/health/live` and `/health/ready` return the expected status without leaking secrets. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 7 | A happy-path and a mandatory-stop case complete with exact audit chain verification. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 8 | A valid non-self reviewer can create a test-only disposition with required rationale and two distinct audits. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 9 | The emergency kill switch blocks intake, processing and disposition as designed. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 10 | A PostgreSQL backup can be restored into a separate local test database, and audit-chain verification still succeeds. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 11 | A rollback or redeploy to the previous pinned image and configuration is documented and tested where two builds are available. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| 12 | English and Arabic reflow, keyboard navigation, focus states, contrast, colour-independent status and reduced motion have passed a smoke test. | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` |

### 3.1 Confirmation aggregate counts

| Measure | Numerator | Denominator | Value |
|---|---|---|---|
| Confirmations defined | 12 | 12 | 12 |
| Confirmations executed | `<PENDING>` | 12 | `<NOT_RUN>` |
| Confirmations recorded `PASS` | `<PENDING>` | 12 | `<NOT_RUN>` |
| Confirmations recorded `FAIL` | `<PENDING>` | 12 | `<NOT_RUN>` |
| Confirmations recorded `BLOCKED` | `<PENDING>` | 12 | `<NOT_RUN>` |
| Confirmations recorded `NOT_RUN` | 12 | 12 | 12 |

---

## 4. Supporting detail for each confirmation

Complete the subsections below. They record the specific observations that make each numbered confirmation auditable.

### 4.1 Clean build (confirmation 1)

| Field | Value |
|---|---|
| Commands executed, in order | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Lockfiles honoured without resolution drift | `<NOT_RUN>` |
| Build warnings or errors recorded | `<PENDING>` |
| Total build duration | `<PENDING>` |
| Build transcript artifact and SHA-256 | `<PENDING>` |

### 4.2 Migrations and seed (confirmation 2)

| Field | Value |
|---|---|
| Migration command and final revision reached | `<PENDING>` |
| Migration rollback tested to the previous revision | `<NOT_RUN>` |
| Seed command and outcome | `<PENDING>` |
| Manifest hash validation outcome for every source version | `<NOT_RUN>` |
| Behaviour observed when a source file is deliberately altered before seeding | `<NOT_RUN>` |
| Append-only audit protection verified after migration | `<NOT_RUN>` |
| Transcript artifact and SHA-256 | `<PENDING>` |

### 4.3 Default mock mode start (confirmation 3)

| Field | Value |
|---|---|
| `MODEL_MODE` observed at start | `<PENDING>` |
| Credentials present in the environment at start | `<PENDING>` |
| Outbound access available to the container during the test | `<PENDING>` |
| A full case completed with no outbound connection attempt observed | `<NOT_RUN>` |
| Transcript artifact and SHA-256 | `<PENDING>` |

### 4.4 Prohibited connector and egress inventory (confirmations 3, 4 and 5)

Cross-check against `SECURITY_BOUNDARIES.md` and the completed `security_test_report.md`. Record what was observed in the running image, not what the documentation states.

| ID | Prohibited integration or path | Inspection performed in the running image | Present in the runtime image | Egress attempt observed | Result | Evidence link and SHA-256 |
|---|---|---|---|---|---|---|
| `DV-PC-01` | Email, SMS, chat or notification service | `<PENDING>` | `<NOT_ASSESSED>` | `<NOT_ASSESSED>` | `NOT_RUN` | `<PENDING>` |
| `DV-PC-02` | Webhook or generic HTTP action tool | `<PENDING>` | `<NOT_ASSESSED>` | `<NOT_ASSESSED>` | `NOT_RUN` | `<PENDING>` |
| `DV-PC-03` | Public web search, browser or scraper | `<PENDING>` | `<NOT_ASSESSED>` | `<NOT_ASSESSED>` | `NOT_RUN` | `<PENDING>` |
| `DV-PC-04` | Payment, procurement or transaction service | `<PENDING>` | `<NOT_ASSESSED>` | `<NOT_ASSESSED>` | `NOT_RUN` | `<PENDING>` |
| `DV-PC-05` | Operational database write or external DSN configuration | `<PENDING>` | `<NOT_ASSESSED>` | `<NOT_ASSESSED>` | `NOT_RUN` | `<PENDING>` |
| `DV-PC-06` | Repository mutation, upload endpoint or dynamic source ingestion | `<PENDING>` | `<NOT_ASSESSED>` | `<NOT_ASSESSED>` | `NOT_RUN` | `<PENDING>` |
| `DV-PC-07` | OAuth or real identity provider integration | `<PENDING>` | `<NOT_ASSESSED>` | `<NOT_ASSESSED>` | `NOT_RUN` | `<PENDING>` |
| `DV-PC-08` | External telemetry or crash reporting | `<PENDING>` | `<NOT_ASSESSED>` | `<NOT_ASSESSED>` | `NOT_RUN` | `<PENDING>` |
| `DV-PC-09` | Model tool or function calling | `<PENDING>` | `<NOT_ASSESSED>` | `<NOT_ASSESSED>` | `NOT_RUN` | `<PENDING>` |
| `DV-PC-10` | Provider or model fallback | `<PENDING>` | `<NOT_ASSESSED>` | `<NOT_ASSESSED>` | `NOT_RUN` | `<PENDING>` |

| Egress and configuration check | Result | Evidence link and SHA-256 |
|---|---|---|
| Default egress is denied and the stack still functions in mock mode | `NOT_RUN` | `<PENDING>` |
| In optional live mode, exactly one named endpoint is permitted | `NOT_RUN` | `<PENDING>` |
| In optional live mode, an unavailable endpoint produces a reason-coded closed failure with no fallback | `NOT_RUN` | `<PENDING>` |
| Configuration and secret inventory recorded, with no secret value written into this checklist | `NOT_RUN` | `<PENDING>` |
| `.env.example` contains placeholders only | `NOT_RUN` | `<PENDING>` |
| Database is not exposed publicly | `NOT_RUN` | `<PENDING>` |
| No privileged container mode is used | `NOT_RUN` | `<PENDING>` |
| Source corpus mount is read-only at runtime | `NOT_RUN` | `<PENDING>` |

### 4.5 Health endpoints (confirmation 6)

| Field | Value |
|---|---|
| `/health/live` status code and body observed | `<PENDING>` |
| `/health/ready` status code and body observed | `<PENDING>` |
| Behaviour observed with the database stopped | `<PENDING>` |
| Secrets, connection strings, versions or internal paths leaked in either response | `<NOT_ASSESSED>` |
| Transcript artifact and SHA-256 | `<PENDING>` |

### 4.6 Case execution and audit verification (confirmation 7)

| Field | Happy path | Mandatory stop |
|---|---|---|
| Case ID | `<PENDING>` | `<PENDING>` |
| Scenario reference from the TEVV matrix | `<PENDING>` | `<PENDING>` |
| Terminal state observed | `<PENDING>` | `<PENDING>` |
| Route observed | `<PENDING>` | `<PENDING>` |
| Reason code observed | `<PENDING>` | `<PENDING>` |
| Packet ID, version and SHA-256 | `<PENDING>` | `<NOT_APPLICABLE: reason required if no packet>` |
| Audit chain verification command and outcome | `<NOT_RUN>` | `<NOT_RUN>` |
| First divergence reported, if any | `<PENDING>` | `<PENDING>` |
| Transcript artifact and SHA-256 | `<PENDING>` | `<PENDING>` |

### 4.7 Reviewer disposition (confirmation 8)

| Field | Value |
|---|---|
| Reviewer identity used | `<PENDING>` |
| Requester identity used, confirmed to be a different identity | `<NOT_RUN>` |
| Disposition value recorded | `<PENDING>` |
| Rationale supplied and stored | `<NOT_RUN>` |
| Behaviour observed when rationale is omitted | `<NOT_RUN>` |
| Behaviour observed when the requester attempts self-review | `<NOT_RUN>` |
| Pre-issuance audit event confirmed, with type and timestamp | `<PENDING>` |
| Closure audit event confirmed, with type and timestamp, and later than the pre-issuance event | `<PENDING>` |
| Any external side effect observed after disposition | `<NOT_ASSESSED>` |
| Transcript artifact and SHA-256 | `<PENDING>` |

### 4.8 Kill switch (confirmation 9)

| Field | Value |
|---|---|
| Administrator identity used to toggle the kill switch | `<PENDING>` |
| Audit event recorded for the toggle | `<PENDING>` |
| Intake attempted while active, and outcome | `<NOT_RUN>` |
| Processing attempted while active, and outcome | `<NOT_RUN>` |
| Disposition attempted while active, and outcome | `<NOT_RUN>` |
| Reason code observed | `<PENDING>` |
| Behaviour observed after the switch is released | `<NOT_RUN>` |
| Transcript artifact and SHA-256 | `<PENDING>` |

### 4.9 Backup and restore (confirmation 10)

| Field | Value |
|---|---|
| Backup command and artifact reference | `<PENDING>` |
| Backup artifact SHA-256 | `<PENDING>` |
| Separate local test database used for the restore | `<PENDING>` |
| Restore command and outcome | `<NOT_RUN>` |
| Audit chain verification outcome after restore | `<NOT_RUN>` |
| Row counts compared before and after restore | `<PENDING>` |
| Append-only protections still enforced after restore | `<NOT_RUN>` |
| Transcript artifact and SHA-256 | `<PENDING>` |

### 4.10 Rollback and redeploy (confirmation 11)

| Field | Value |
|---|---|
| Two builds available for comparison | `<NOT_ASSESSED>` |
| Previous pinned image digests and configuration reference | `<PENDING>` |
| Documented rollback procedure reference | `<PENDING>` |
| Rollback executed and outcome | `<NOT_RUN>` |
| Redeploy to the current build executed and outcome | `<NOT_RUN>` |
| Migration compatibility observed across the rollback | `<PENDING>` |
| If only one build exists, the recorded reason and the planned date for this confirmation | `<NOT_APPLICABLE: reason required if selected>` |
| Transcript artifact and SHA-256 | `<PENDING>` |

### 4.11 Accessibility and bilingual smoke test (confirmation 12)

| Check | Method | Result | Evidence link and SHA-256 |
|---|---|---|---|
| English layout reflow at the required breakpoints and text scaling | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| Arabic layout mirroring, directionality and line height | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| Keyboard navigation across every required route | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| Visible focus indicators | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| WCAG 2.2 AA contrast | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| Status conveyed by text, icon and shape rather than colour alone | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| Grayscale legibility | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| Reduced-motion preference respected | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| Fixed packet notices rendered in both languages | `<PENDING>` | `NOT_RUN` | `<PENDING>` |
| No merged or generic readiness indicator present in any view | `<PENDING>` | `NOT_RUN` | `<PENDING>` |

---

## 5. Transcript and log index

Every transcript and log must be retained unmodified and hashed. Failed runs are retained visibly and are never overwritten.

| Artifact ID | Description | Path | SHA-256 | Timestamp (UTC) | Indexed in `release_evidence_index.json` |
|---|---|---|---|---|---|
| `EXAMPLE-000` | ILLUSTRATIVE ROW ONLY. Remove before use. | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

---

## 6. Defects raised by this gate

Every `FAIL` must produce at least one defect record in `artifacts/templates/defect_register.csv`.

| Defect ID | Confirmation number | Severity | Description | Affected component and version | Containment | Owner | Retest reference | Status |
|---|---|---|---|---|---|---|---|---|
| `EXAMPLE-000` | `<PENDING>` | `<PENDING>` | ILLUSTRATIVE ROW ONLY. Remove before use. This row records no defect and no result. | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

| Severity | Count raised | Count open | Count closed | Blocks acceptance while open |
|---|---|---|---|---|
| `S0_CRITICAL` | `<PENDING>` | `<PENDING>` | `<PENDING>` | Yes |
| `S1_HIGH` | `<PENDING>` | `<PENDING>` | `<PENDING>` | Yes |
| `S2_MODERATE` | `<PENDING>` | `<PENDING>` | `<PENDING>` | Recorded as a condition or a limitation |
| `S3_LOW` | `<PENDING>` | `<PENDING>` | `<PENDING>` | Recorded as a limitation |

---

## 7. Retest record

| Round | Date (UTC) | Validator | Commit SHA and image digests | Confirmations retested | Confirmations now `PASS` | Confirmations still `FAIL` | New defects raised | Round outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | `<PENDING>` | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| 2 | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

| Field | Value |
|---|---|
| Location of retained superseded rounds | `<PENDING>` |
| Confirmation that no earlier round was overwritten | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR: CONFIRMED / NOT_CONFIRMED + explanation>` |

---

## 8. Validator conclusion

| Field | Value |
|---|---|
| Overall deployment validation state | `NOT_STARTED` |
| Basis for the stated conclusion, in the validator's own words | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Confirmations remaining `NOT_RUN` at conclusion, and why | `<PENDING>` |
| Open `S0_CRITICAL` and `S1_HIGH` defects at conclusion | `<PENDING>` |
| Limits of this validation that a later reader must know | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |

Overall state vocabulary: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `CONCLUDED_WITH_OPEN_DEFECTS`, `CONCLUDED_WITH_CONFIRMATIONS_OUTSTANDING`, `CONCLUDED_ALL_CONFIRMATIONS_RECORDED_AT_THIS_VERSION`. The default is `NOT_STARTED`.

This conclusion applies only to the exact commit, image digests, configuration and clean environment recorded above. It supports deployment-validation evidence for an isolated synthetic prototype and nothing further.

---

## 9. Status dimensions

The four dimensions are independent and are recorded separately. They must never be merged, averaged or rendered as a single readiness state (INV-14).

| Dimension | Permitted values (Section 7.1) | Default | Current value |
|---|---|---|---|
| Built | `NOT_EVIDENCED` / `PARTIALLY_EVIDENCED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` |
| Integration | `NOT_EVIDENCED` / `PARTIALLY_EVIDENCED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` |
| Operational | `NOT_EVIDENCED` / `HISTORICAL_CONFIRMED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` |
| Authorization | `NOT_GRANTED` / `GRANTED_WITH_CONDITIONS` / `GRANTED` | `NOT_GRANTED` | `NOT_GRANTED` |

Gate G-E produces deployment-validation evidence only. Completing this checklist does not change any dimension above, does not establish Operational status, and confers no authorization.

---

## 10. Signature and date

Signing attests only to the accuracy of the record above. It is not an acceptance of any status claim, and it confers no authority.

| Field | Value |
|---|---|
| Validator name | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Validator function | Independent evaluator or reviewer |
| Signature | `<TO BE COMPLETED BY DEPLOYMENT VALIDATOR>` |
| Date signed (UTC) | `<PENDING>` |
| Commit, image digests and configuration to which this signature is bound | `<PENDING>` |
| Countersigning technical owner (acknowledgement of receipt only) | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Date acknowledged (UTC) | `<PENDING>` |
| Next assurance gate | `G-F — Human-owner evidence acceptance` |

A completed instance of this checklist must be stored as an immutable artifact, listed in `artifacts/templates/evidence_register.csv`, and indexed in `artifacts/templates/release_evidence_index.json` before gate G-F is convened.
