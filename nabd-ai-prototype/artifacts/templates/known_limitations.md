# Known Limitations — NABD AI Decision Review

## 0. Template control block

| Field | Value |
|---|---|
| Template ID | `TPL-KNOWN-LIMITATIONS-V1` |
| Template version | `1.0.0` |
| Template kind | `CONTROL_ARTIFACT` |
| Assurance gates served | Cross-gate input; mandatory input to `G-F — Human-owner evidence acceptance` |
| Environment | `ISOLATED_PROTOTYPE_V1` |
| Data boundary | `SYNTHETIC_ONLY` |
| Business scope | `BUSINESS_UNIT_V1` |
| Controlling specification | `docs/NABD_AI_CURSOR_FULL_PROTOTYPE_BUILD_SPEC.md`, Sections 1, 2, 3, 7.1, 15.1, 16.2, 17, 17.1, 18, 23 |
| Completion state | `<PENDING>` |

> **Control artifact notice.** This template is a control artifact. It does not itself constitute evidence, and its presence in the repository does not indicate that the limitations below have been assessed, that any exclusion has been verified, or that any status dimension has changed. A limitations record exists only when a named preparer has completed every field below for a specific component version set and a named independent reviewer has confirmed it is complete and accurate.

### 0.1 Placeholder tokens

Every cell must carry a value before the record is considered complete. An unpopulated cell is read as `<PENDING>` and never as an absence of limitation.

| Token | Meaning |
|---|---|
| `<TO BE COMPLETED BY TECHNICAL OWNER>` | The technical owner supplies the value. |
| `<TO BE COMPLETED BY INDEPENDENT EVALUATOR>` | A named independent evaluator, reviewer, security tester or deployment validator supplies the value. |
| `<PENDING>` | Not yet determined. |
| `<NOT_RUN>` | The activity has not been executed. |
| `<NOT_ASSESSED>` | The item has not been examined. |
| `<NONE_RECORDED>` | Deliberately empty at completion time; must be affirmed by the completer. |
| `<NOT_APPLICABLE: reason>` | Requires a written reason. A bare `NOT_APPLICABLE` is invalid. |

### 0.2 Purpose and standing

This record states, in one place, what the NABD AI Decision Review prototype excludes by design, what has not been evaluated, and what risk remains. It is written so that a later reader who did not build the prototype can tell the difference between a control that was tested, a control that was designed but not tested, and a capability that does not exist.

An empty section in this record is not a statement that no limitation exists. It is a statement that no limitation has been recorded, which is itself a limitation.

---

## 1. Independence declaration

### 1.1 Three-function separation (Section 17)

- The **technical owner** prepares code and developer evidence.
- The **independent evaluator or reviewer** reviews code, security, TEVV and deployment results.
- The **human owner or delegate** accepts or rejects a narrow evidence or status claim.

One identity must not perform all three functions for the same component, version, status dimension and evidence set. Invariant INV-16 prohibits self-acceptance: a developer, model, evaluator, administrator or evidence record cannot accept its own status claim.

Applied to this record: the party who prepares the limitations record must not be the sole party who confirms it is complete, and neither may act as the human owner or delegate who accepts the evidence that this record constrains. A limitations record confirmed only by its own author is not confirmed.

| Function | Named identity | Responsibility for this record | Distinct from the other two functions |
|---|---|---|---|
| Technical owner | `<TO BE COMPLETED BY TECHNICAL OWNER>` | Prepares and maintains the entries below. | `<PENDING>` |
| Independent evaluator or reviewer | `<TO BE COMPLETED BY INDEPENDENT EVALUATOR>` | Confirms that the entries are complete, accurate and consistent with the gate records. | `<PENDING>` |
| Human owner or delegate | `<PENDING>` | Reads this record before recording a decision. Does not author it. | `<PENDING>` |

| Declaration | Response |
|---|---|
| Every limitation identified during gates G-A to G-E has been carried into this record | `<TO BE COMPLETED BY INDEPENDENT EVALUATOR: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Every open residual risk in the security test report appears in Section 6 below | `<TO BE COMPLETED BY INDEPENDENT EVALUATOR: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Every acceptance target marked `COVERAGE_INCOMPLETE` in the TEVV report appears in Section 7 below | `<TO BE COMPLETED BY INDEPENDENT EVALUATOR: CONFIRMED / NOT_CONFIRMED + explanation>` |
| No limitation has been removed, softened or merged since the previous version of this record | `<TO BE COMPLETED BY INDEPENDENT EVALUATOR: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Any exception to independence, and the compensating control applied | `<PENDING>` |

---

## 2. V1 binding boundary exclusions (Section 1)

The prototype implements a bounded V1 control thesis. It is not the future general product. The table below restates the binding boundary. Each row states what is implemented and what is excluded; nothing in the excluded column exists in V1.

| Boundary | Implemented in V1 | Excluded from V1 | Verification state |
|---|---|---|---|
| Environment | `ISOLATED_PROTOTYPE_V1` local Docker workbench | Any production, pilot, customer or institutional environment | `<NOT_ASSESSED>` |
| Data | `SYNTHETIC_ONLY`; versioned frozen source corpus | Live uploads, dynamic ingestion, real documents, public web content | `<NOT_ASSESSED>` |
| Business scope | `BUSINESS_UNIT_V1` only | Multi-tenant or cross-unit enterprise operation | `<NOT_ASSESSED>` |
| Question | One bounded internal policy or SOP evidence question | Open-ended advice and action-seeking questions | `<NOT_ASSESSED>` |
| AI calls | A maximum of two calls: draft, then verifier | Agent loops, a third refiner call, model-selected tools | `<NOT_ASSESSED>` |
| Model configuration | Exactly one pinned configuration per run | Runtime switching, provider or model fallback | `<NOT_ASSESSED>` |
| Outputs | A Decision Readiness Packet and controlled test records | Approval, execution, message, transaction, activation | `<NOT_ASSESSED>` |
| Route | `HUMAN_REVIEW_REQUIRED` or `CANNOT_PROCEED` | Any score that overrides a mandatory stop | `<NOT_ASSESSED>` |
| Disposition | `RETURN_FOR_CLARIFICATION`, `ACCEPT_AS_TEST_EVIDENCE`, `REJECT_AS_TEST_EVIDENCE` | Approving an action, sending, paying, updating a record, or activating anything | `<NOT_ASSESSED>` |

### 2.1 Data the prototype does not use

The prototype does not use real, personal, customer, confidential, institutional, clinical, legal, financial or production data. All content in the frozen corpus is synthetic and was created for testing. No conclusion drawn from that corpus describes any real policy, procedure, organisation or person.

### 2.2 Systems the prototype does not connect to

The prototype does not connect to a customer identity provider, document repository, email service, messaging platform, ticketing system, webhook, payment service, operational database, browser, search engine, or any other external action service.

---

## 3. Prohibited connections excluded by design (Section 15.1)

None of the following exists in the runtime image as a package module, environment variable, route, dependency configuration or network destination. Each row must be confirmed by the completed `security_test_report.md` and cross-checked by the completed `deployment_validation_checklist.md`. Until those records are completed, the verification state remains `NOT_RUN`.

| ID | Prohibited integration or path | Required enforcement | Verification state | Evidence reference |
|---|---|---|---|---|
| `KL-PC-01` | Email, SMS, chat or notification service | No SDK or dependency, no route, deny test | `<NOT_RUN>` | `<PENDING>` |
| `KL-PC-02` | Webhook or generic HTTP action tool | No outbound action client, allowlist test | `<NOT_RUN>` | `<PENDING>` |
| `KL-PC-03` | Public web search, browser or scraper | No dependency or route | `<NOT_RUN>` | `<PENDING>` |
| `KL-PC-04` | Payment, procurement or transaction service | No dependency, route or schema field | `<NOT_RUN>` | `<PENDING>` |
| `KL-PC-05` | Operational database write | Separate demo database only; no external DSN configuration | `<NOT_RUN>` | `<PENDING>` |
| `KL-PC-06` | Repository mutation or dynamic source ingestion | No upload endpoint; source directory read-only at runtime | `<NOT_RUN>` | `<PENDING>` |
| `KL-PC-07` | OAuth or real identity provider integration | Synthetic server sessions only | `<NOT_RUN>` | `<PENDING>` |
| `KL-PC-08` | External telemetry or crash reporting | Disabled; local structured logs only | `<NOT_RUN>` | `<PENDING>` |
| `KL-PC-09` | Model tool or function calling | Explicitly disabled; output schema rejects tool requests | `<NOT_RUN>` | `<PENDING>` |
| `KL-PC-10` | Provider or model fallback | Adapter rejects any configuration mismatch | `<NOT_RUN>` | `<PENDING>` |

The consequence of these exclusions is that the prototype has no mechanism by which a decision, a packet, a disposition or a model output can reach an operational system. This is a design property, not a runtime setting, and it is the reason no disposition can unlock execution (INV-12).

---

## 4. Unevaluated elements

An element listed here has not been evaluated. It has not been shown to work and it has not been shown to fail. Do not treat an unevaluated element as either.

| ID | Element | Why it is unevaluated | Evaluation state | Gate that would evaluate it | Owner | Planned action |
|---|---|---|---|---|---|---|
| `KL-UE-01` | Live-model behaviour under any provider or model | The default deterministic mock mode makes no outbound model call | `NOT_RUN` | `G-D` | `<PENDING>` | `<PENDING>` |
| `KL-UE-02` | Behaviour with non-synthetic content of any kind | The corpus is frozen and synthetic; there is no ingestion path | `NOT_RUN` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `KL-UE-03` | Behaviour at institutional data volume or concurrency | Concurrency is capped at two cases by design | `NOT_RUN` | `G-D` | `<PENDING>` | `<PENDING>` |
| `KL-UE-04` | Long-running operational reliability, availability and recovery | The prototype has no operational use to observe | `NOT_RUN` | `<NOT_APPLICABLE: no operational use exists>` | `<PENDING>` | `<PENDING>` |
| `KL-UE-05` | Monitoring, alerting and incident response maturity | Out of scope for an isolated prototype | `NOT_RUN` | `<NOT_APPLICABLE: out of V1 scope>` | `<PENDING>` | `<PENDING>` |
| `KL-UE-06` | Vector retrieval behaviour | `ENABLE_VECTOR_RETRIEVAL` is disabled by default and cannot be required for any test to pass | `NOT_RUN` | `G-D` | `<PENDING>` | `<PENDING>` |
| `KL-UE-07` | Multi-tenant or cross-unit isolation | Only `BUSINESS_UNIT_V1` exists | `NOT_RUN` | `G-C` | `<PENDING>` | `<PENDING>` |
| `KL-UE-08` | Real identity provider, session and credential handling | Synthetic server sessions only | `NOT_RUN` | `G-C` | `<PENDING>` | `<PENDING>` |
| `KL-UE-09` | Adversarial behaviour of a live model against the containment controls | No live model is exercised | `NOT_RUN` | `G-C` | `<PENDING>` | `<PENDING>` |
| `KL-UE-10` | Accessibility beyond the recorded smoke test | Only a smoke test is required at gate G-E | `NOT_RUN` | `G-E` | `<PENDING>` | `<PENDING>` |
| `KL-UE-11` | Arabic linguistic quality of generated summaries | Not a control property and not measured | `NOT_RUN` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `KL-UE-12` | Third-party assessment or external conformity assessment | None has been sought, performed or claimed | `NOT_RUN` | `<NOT_APPLICABLE: out of V1 scope>` | `<PENDING>` | `<PENDING>` |
| `KL-UE-13` | Rollback behaviour where only one build exists | Confirmation 11 of Section 18 requires two builds | `NOT_RUN` | `G-E` | `<PENDING>` | `<PENDING>` |
| `KL-UE-14` | Backup and restore beyond a single local test database | Only the local restore path is in scope | `NOT_RUN` | `G-E` | `<PENDING>` | `<PENDING>` |
| `<PENDING>` | `<PENDING>` | `<PENDING>` | `NOT_RUN` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

---

## 5. Live-model evaluation status

| Field | Value |
|---|---|
| Default model mode | `mock` (deterministic mock adapter, in process) |
| Live-model evaluation | `NOT_RUN` |
| Reason | Live-model evaluation is `NOT_RUN` in the default deterministic mock mode. No credential is required, requested or present; the optional adapter is disabled unless `MODEL_MODE=live` and every explicit endpoint and model variable is supplied; and the container is expected to run with no outbound internet access. |
| Optional live mode, if ever exercised | One configured HTTPS endpoint and one configured model only. No discovery, no tool use, no browsing, no retry against another model and no fallback. |
| Model configuration IDs exercised in mock mode | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Scenarios that would require re-execution under a live model | `<TO BE COMPLETED BY INDEPENDENT EVALUATOR>` |

What mock-mode results do and do not show:

1. They exercise the deterministic control system that surrounds the model: evidence admission, eligibility filtering, exact citation binding, schema enforcement, rule precedence, routing, packet validation, dual audit and fail-closed behaviour.
2. They exercise the declared fault modes of the mock adapter, including timeout, malformed response, refusal, disagreement, fabricated citation and resource-limit conditions.
3. They do **not** measure the behaviour, accuracy, calibration or failure distribution of any live language model.
4. They do **not** support any statement about how a live model would behave against the same corpus, question set or adversarial inputs.
5. A result obtained in mock mode must never be presented as a live-model result.

---

## 6. Non-production boundary

| Statement | Detail |
|---|---|
| The prototype is not in operational use | `ISOLATED_PROTOTYPE_V1` is a local Docker workbench with synthetic data. It carries no institutional workload. |
| The prototype is not authorized | Authorization is `NOT_GRANTED`. The `SYNTHETIC_DEMO_AUTHORIZATION` fixture is a build-controlled test fixture; it is not human-owner acceptance, deployment authorization or institutional authority. |
| Deployment does not change authority | Local, hosted, on-premises and offline deployment share the non-execution rule (INV-15). Moving the prototype to a different host changes nothing about its authority. |
| A demonstration is not evidence | A working application, a successful continuous integration run, a generated summary or a live demonstration does not satisfy any assurance gate by itself. |
| The seal is tamper-evidence only | The packet SHA-256 and the audit hash chain are tamper-evidence references. They are not proof of truth, proof of immutable storage, authorization or authorship, and they require controlled storage and independent verification. |
| The injection detector is defence in depth | The deterministic instruction-like content detector reduces exposure. It is not a source-authority decision-maker and does not determine whether a source may be relied upon. |
| Passing deployment validation is bounded | Completing the Section 18 checklist supports deployment-validation evidence for an isolated prototype only. It does not establish Operational status, service monitoring, incident response maturity, customer data approval, or authorization to use the prototype outside its synthetic environment. |
| Human authority is retained | The prototype supports and prepares decisions. Authorized people retain final authority, and any institutional action happens separately under another procedure (INV-01). |

---

## 7. Measurement and coverage limitations

| ID | Limitation | Detail | State |
|---|---|---|---|
| `KL-ML-01` | Percentage-only reporting is prohibited | A measured value must always carry its exact numerator and denominator. A percentage presented without a denominator is not a result. | Standing rule |
| `KL-ML-02` | Benign frozen-case completion threshold | The 95 per cent target applies only when at least 60 unique benign frozen cases are implemented. Below that count, the denominator must be reported and the threshold marked `COVERAGE_INCOMPLETE`. | `COVERAGE_INCOMPLETE` until the implemented count is recorded and confirmed |
| `KL-ML-03` | Labelled claim-support classification threshold | The 95 per cent target applies only when adequately labelled case volume exists. Otherwise the denominator must be reported and coverage marked incomplete. | `COVERAGE_INCOMPLETE` until the labelled volume is recorded and justified |
| `KL-ML-04` | Targets are prototype targets, not field performance | Every Section 16.2 target is measured against a frozen synthetic fixture set. None describes behaviour on real data, in a real environment, or at institutional scale. | Standing limitation |
| `KL-ML-05` | Evidence is version-bound | A gate result applies only to the exact component, model, rule, prompt, schema and corpus versions it exercised. It does not carry forward to any other version set. | Standing rule |
| `KL-ML-06` | Determinism is a property of the mock configuration | Reproducibility observed across repetitions reflects the deterministic mock adapter and the frozen fixtures, not model stability in general. | Standing limitation |
| `KL-ML-07` | Absolute-accuracy claims are not made | No claim of absolute correctness, absolute containment or absolute absence of fabrication is made or supported. The controls are measurable thresholds and fail-closed behaviours, not guarantees. | Standing rule |
| `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

---

## 8. Remaining risks

Recording a risk here is not acceptance of it. Acceptance occurs only in a completed `human_owner_acceptance_record.md`, and only for the narrow claim stated there.

| Risk ID | Description | Category | Source gate | Existing containment | Residual exposure | Detection or verification method | Owner | Review date | State |
|---|---|---|---|---|---|---|---|---|---|
| `EXAMPLE-000` | ILLUSTRATIVE ROW ONLY. Remove before use. This row records no risk and no position. | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `KL-RR-01` | A control that has been designed but not yet independently tested may not behave as designed | Assurance coverage | `<PENDING>` | Assurance gates G-B to G-E | `<PENDING>` | Completion of the gate records | `<PENDING>` | `<PENDING>` | `IDENTIFIED` |
| `KL-RR-02` | A reader may mistake a mock-mode result for a live-model result | Interpretation | `G-D` | Explicit `NOT_RUN` recording in every report | `<PENDING>` | Review of any external summary before circulation | `<PENDING>` | `<PENDING>` | `IDENTIFIED` |
| `KL-RR-03` | A reader may mistake a synthetic-corpus measurement for field performance | Interpretation | `G-D` | Fixed notices, coverage flags and denominator reporting | `<PENDING>` | Review of any external summary before circulation | `<PENDING>` | `<PENDING>` | `IDENTIFIED` |
| `KL-RR-04` | A consumer of the status data may merge the four dimensions into a single indicator | Interpretation | Cross-gate | INV-14; separate fields in every artifact and interface | `<PENDING>` | Interface and document review | `<PENDING>` | `<PENDING>` | `IDENTIFIED` |
| `KL-RR-05` | A future change may weaken a boundary without a corresponding gate re-run | Change control | Cross-gate | Version-bound evidence; re-acceptance triggers | `<PENDING>` | Version fingerprint comparison at each gate | `<PENDING>` | `<PENDING>` | `IDENTIFIED` |
| `KL-RR-06` | The synthetic corpus may not represent the ambiguity, conflict and drift present in real source material | Representativeness | `G-D` | Deliberate inclusion of superseded, revoked, cross-scope, conflicting and quarantined fixtures | `<PENDING>` | Corpus adequacy declaration in the TEVV report | `<PENDING>` | `<PENDING>` | `IDENTIFIED` |
| `KL-RR-07` | The deterministic injection detector may not recognise a novel instruction-like pattern | Security | `G-C` | Quarantine, untrusted-content marking, schema enforcement, output containment, no connector | `<PENDING>` | Adversarial corpus execution and expansion | `<PENDING>` | `<PENDING>` | `IDENTIFIED` |
| `KL-RR-08` | A dependency advisory may be published after the recorded scan window | Supply chain | `G-C` | Pinned lockfiles and image digests; scan record with an explicit window | `<PENDING>` | Re-scan at each review date | `<PENDING>` | `<PENDING>` | `IDENTIFIED` |
| `KL-RR-09` | An unresolved `S0_CRITICAL` or `S1_HIGH` defect may be overlooked at the acceptance gate | Assurance process | `G-F` | Blocking rule; explicit blocking check in the acceptance record | `<PENDING>` | Defect register cross-check before any decision | `<PENDING>` | `<PENDING>` | `IDENTIFIED` |
| `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

Risk state vocabulary: `IDENTIFIED`, `TREATMENT_PROPOSED`, `TREATMENT_IN_PROGRESS`, `PROPOSED_FOR_OWNER_DECISION`, `ACCEPTED_WITH_CONDITIONS`, `REJECTED`, `CLOSED_BY_CORRECTION`. The default is `IDENTIFIED`.

---

## 9. Future-gated options

### 9.1 The final implementation directive (Section 23)

> Build the **smallest complete, secure-by-design, synthetic-only NABD AI workbench** that demonstrates evidence admission before reasoning, claim-to-evidence binding, deterministic rule precedence, visible uncertainty, verified human review, dual audit, and terminal non-execution. Preserve every mandatory boundary. Prefer a smaller tested control system over a broader agentic product.

### 9.2 The recording rule

If a feature request conflicts with the directive above, the control boundary is retained and the requested feature is recorded here as a **future-gated option** rather than being added to V1. This is the only route for such a request. It is not a queue that empties by default: an option recorded here remains excluded until the prerequisites beside it have been satisfied and a separate decision is taken under a later version's own assurance process.

Recording an option here is not agreement to build it, is not a commitment, and does not indicate that the option is safe or desirable. It is a record that the request was made, that it conflicts with a boundary, and that the boundary was retained.

| Rule | Detail |
|---|---|
| Where a conflicting request is recorded | This section, with a unique `KL-FG-` identifier. |
| What must never happen instead | Adding the feature to V1, weakening a boundary to accommodate it, or implementing it behind an undocumented flag. |
| Who may record an option | Any party. The technical owner maintains the register. |
| Who may reclassify an option | Not this record. Reclassification requires a later version scope with its own assurance gates and its own human-owner decision. |
| Standing constraint | Any option that would remove or weaken an invariant in Section 3 remains excluded regardless of prerequisites. |

### 9.3 Standing future-gated options

These options are already identified as conflicting with the V1 directive or the V1 boundary. They are excluded from V1.

| ID | Requested option | Conflicts with | Boundary retained instead | Prerequisites before it could be reconsidered | Decision |
|---|---|---|---|---|---|
| `KL-FG-01` | Multiple model providers with adapter switching | One pinned configuration per run; no runtime switching | A single pinned configuration per task role, with a new configuration ID for any material change | A configuration governance model, per-provider evaluation and a re-run of every security and TEVV gate per provider | `FUTURE_GATED` |
| `KL-FG-02` | Provider or model fallback on failure | No fallback; fail closed | A reason-coded closed failure with at most one same-endpoint retry | A defined failure taxonomy and evidence that fallback cannot change the evidence basis of a claim | `FUTURE_GATED` |
| `KL-FG-03` | A three-stage refinement path with a third model call | A maximum of two model calls per case | Draft, then independent verification, then deterministic rules | A demonstrated control benefit that deterministic rules cannot provide, plus a revised call budget and limits | `FUTURE_GATED` |
| `KL-FG-04` | Model-selected tools or function calling | Code controls the workflow (INV-03); tool calling disabled | A finite-state machine that owns every transition | A containment model for tool selection that does not let a model choose a state or an action | `FUTURE_GATED` |
| `KL-FG-05` | Agent loops or autonomous multi-step execution | Fixed orchestrator; two calls maximum | A deterministic ordered workflow | Out of scope for the V1 control thesis; would require a different control thesis entirely | `FUTURE_GATED` |
| `KL-FG-06` | An approval action in the disposition console | Review never unlocks execution (INV-12); test-only dispositions | `RETURN_FOR_CLARIFICATION`, `ACCEPT_AS_TEST_EVIDENCE`, `REJECT_AS_TEST_EVIDENCE` | Excluded by invariant. Any institutional action remains a separate procedure outside this system | `FUTURE_GATED` |
| `KL-FG-07` | Downstream action connectors: email, messaging, ticketing, webhook, payment, record update | Section 15.1 prohibited-connection inventory | No connector exists; an attempted path raises `PATH-001` and an `S0_CRITICAL` security event | Excluded by invariant for the V1 control thesis | `FUTURE_GATED` |
| `KL-FG-08` | Runtime document upload and dynamic source ingestion | Frozen corpus; build-time seeding only | A versioned manifest with hash validation and a read-only source directory | A source governance model covering provenance, lifecycle, access labelling and hash validation at ingestion time | `FUTURE_GATED` |
| `KL-FG-09` | Public web search, browsing or scraping as an evidence source | Evidence precedes reasoning (INV-04); frozen eligible sources only | Deterministic retrieval over manifest-listed active source versions | An eligibility model for unbounded sources, which the V1 thesis does not attempt | `FUTURE_GATED` |
| `KL-FG-10` | Real, customer or institutional data | `SYNTHETIC_ONLY` data boundary | A synthetic corpus created for testing | A data protection assessment, a lawful basis, a real environment and an entirely separate authorization process | `FUTURE_GATED` |
| `KL-FG-11` | Real-world pilot cases | Isolated prototype environment | Frozen synthetic scenarios | A different environment, a different authorization and a different assurance programme | `FUTURE_GATED` |
| `KL-FG-12` | Multi-tenant or cross-business-unit operation | `BUSINESS_UNIT_V1` only | Single-scope operation with scope filtering before retrieval | A tenancy isolation model and cross-scope disclosure testing at the new boundary | `FUTURE_GATED` |
| `KL-FG-13` | An unqualified absolute-accuracy demonstration claim | Approved tone; measurable thresholds rather than guarantees | Measured thresholds reported with numerator and denominator | Excluded permanently. No evidence can support an absolute claim of this kind | `FUTURE_GATED` |
| `KL-FG-14` | Vector retrieval as a required or default path | `ENABLE_VECTOR_RETRIEVAL=false` by default; cannot bypass lexical filters | Deterministic lexical retrieval with a fixed rank and tie-break | Evidence that a vector path cannot bypass eligibility, scope, lifecycle or access filters, plus determinism evidence | `FUTURE_GATED` |
| `KL-FG-15` | A third model-based content detector | No third LLM detector in V1 | A deterministic pattern and heuristic fixture set as defence in depth | A containment model showing the detector cannot itself become an injection surface | `FUTURE_GATED` |
| `KL-FG-16` | Hardware sizing and deployment topology from the roadmap images | Future deployment context only | A local Docker prototype with a mock model baseline | A deployment programme under a later version scope | `FUTURE_GATED` |
| `KL-FG-17` | Commercial planning figures in product or status claims | Planning context only; not a product decision | No commercial figure appears in the product or in any status claim | Not applicable to the product surface at any version | `FUTURE_GATED` |
| `KL-FG-18` | Financial market prediction scope drawn from the contextual research attachment | Excluded from V1 implementation scope | No prediction capability exists | A different product thesis with its own scope and assurance | `FUTURE_GATED` |
| `KL-FG-19` | A single merged status indicator or generic readiness badge | Four independent status dimensions (INV-14) | Four separately rendered dimensions with text, icon and shape | Excluded by invariant | `FUTURE_GATED` |
| `KL-FG-20` | External telemetry, crash reporting or usage analytics | Section 15.1 prohibited-connection inventory | Local structured logs with redaction | A data handling model and an egress policy that the V1 boundary does not permit | `FUTURE_GATED` |

Decision vocabulary for this register: `FUTURE_GATED` (recorded and excluded from V1), `PERMANENTLY_EXCLUDED` (conflicts with an invariant and cannot be reconsidered), `WITHDRAWN` (the requester withdrew the request). The default for a newly recorded option is `FUTURE_GATED`.

### 9.4 Newly recorded options

Append one row per request. Do not edit or remove an earlier row.

| ID | Requested option | Requested by | Date requested (UTC) | Conflict with the Section 23 directive or a V1 boundary | Boundary retained instead | Prerequisites before reconsideration | Decision |
|---|---|---|---|---|---|---|---|
| `EXAMPLE-000` | ILLUSTRATIVE ROW ONLY. Remove before use. This row records no request. | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `FUTURE_GATED` |

---

## 10. Status dimensions

The four dimensions are independent and are recorded separately. They must never be merged, averaged or rendered as a single readiness state (INV-14).

| Dimension | Permitted values (Section 7.1) | Default | Current value |
|---|---|---|---|
| Built | `NOT_EVIDENCED` / `PARTIALLY_EVIDENCED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` |
| Integration | `NOT_EVIDENCED` / `PARTIALLY_EVIDENCED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` |
| Operational | `NOT_EVIDENCED` / `HISTORICAL_CONFIRMED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` |
| Authorization | `NOT_GRANTED` / `GRANTED_WITH_CONDITIONS` / `GRANTED` | `NOT_GRANTED` | `NOT_GRANTED` |

This record does not change any dimension above. It constrains what any dimension may later be claimed to mean.

---

## 11. Maintenance, signature and date

| Field | Value |
|---|---|
| Component version set to which this record applies | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Commit SHA | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Record version | `<PENDING>` |
| Supersedes record version | `<NONE_RECORDED>` |
| Prepared by | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Date prepared (UTC) | `<PENDING>` |
| Independently confirmed complete and accurate by | `<TO BE COMPLETED BY INDEPENDENT EVALUATOR>` |
| Date confirmed (UTC) | `<PENDING>` |
| Next review date | `<PENDING>` |
| Trigger for an out-of-cycle update | Any new limitation, any new residual risk, any newly recorded future-gated option, or any change to a pinned component version. |
| Superseded versions retained without overwriting | `<TO BE COMPLETED BY TECHNICAL OWNER: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Storage location for the completed immutable record | `<PENDING>` |
| Record SHA-256 | `<PENDING>` |
| Listed in `evidence_register.csv` | `<PENDING>` |
| Indexed in `release_evidence_index.json` | `<PENDING>` |
